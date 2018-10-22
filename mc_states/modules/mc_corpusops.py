#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

'''
think to /srv/makina-states/venv/bin/pip install ruamel.yaml
'''


import ruamel.yaml as _y
import re
import os
import logging
from cStringIO import StringIO
re_flags = re.M | re.U | re.S
log = logging.getLogger(__name__)

DEFAULT_COPS_INV = '''
---
compute_nodes_lxcs_makinastates:
  hosts:
    {id_}: {{}}
lxcs_makinastates:
  children:
    {id_}_lxcs_makinastates:
{id_}_lxcs:
  children:
    {id_}_lxcs_makinastates:
{id_}_and_lxcs:
  children:
    {id_}_lxcs:
  hosts:
    {id_}:
{id_}_lxcs_makinastates:
  vars: {{ssh_bastion: {id_}}}
  hosts: {{}}
'''
cops_regs_fw_pref = (
    'corpusops_ms_iptables_registrations_registrations_makinastates')


def export_lxc_compute_node(id_, out_file=None):
    '''Generate corpusops inventory slug to paste inside corpusops compatible inventoy'''
    _s = __salt__
    db = _s['mc_pillar.get_db_infrastructure_maps']()
    cnconf = _s['mc_pillar.get_cloud_entry_for_cn'](id_)
    msiptables = _s['mc_pillar.get_ms_iptables_conf'](id_)
    cfg = _s['mc_utils.cyaml_load'](
        DEFAULT_COPS_INV.format(id_=id_))
    rules = msiptables.get(
        'makina-states.services.firewall.ms_iptables.config', {}
    ).get('rules', [])
    lxcmak = cfg[id_+'_lxcs_makinastates']
    if rules:
        cfg['compute_nodes_lxcs_makinastates'][
            'hosts'
        ][id_].setdefault(cops_regs_fw_pref, {})['rules'] = rules
    else:
        cfg['compute_nodes_lxcs_makinastates']['hosts'][id_] = None
    for vm in cnconf['vms']:
        vmdata = lxcmak['hosts'].setdefault(vm, {})
        domains = _s['mc_pillar.query'](
            'cloud_vm_attrs', {}).get(vm, {}).get('domains', [])
        if vm not in domains:
            domains.insert(0, vm)
        if domains:
            vmdata['haproxy_hosts'] = domains
        vmdata['ssh_port'] = _s['mc_pillar.get_ssh_port'](vm)
        vmdata['local_ip'] = _s['mc_cloud_compute_node.get_ip_for_vm'](
            vm, target=id_)
    if out_file and os.path.exists(out_file):
        with open(out_file) as fic:
            content = fic.read()
        yaml = _y.YAML()
        ncfg = yaml.load(content)
        yaml.preserve_quotes = True
        yaml.explicit_start = True
        yaml.default_flow_style = False
        ncfg = _s['mc_utils.dictupdate'](ncfg, cfg)
        s = StringIO()
        yaml.dump(ncfg, s)
        dcfg = s.getvalue()
    else:
        dcfg = _s['mc_dumper.yaml_dump'](cfg, flow=False)
    dcfg = re.sub(': null$', ':', dcfg, flags=re_flags)
    dcfg = dcfg.replace('\n    ssh_bastion', ' {ssh_bastion')
    dcfg = re.sub('(: {ssh_bastion.*[^}])}.$', '\\1}', dcfg, flags=re_flags)
    if out_file:
        with open(out_file, 'w') as fic:
            fic.write(dcfg)
    return dcfg


def export_lxc_makinastates(export_dir='/tmp', to_file=False):
    out = None
    _s = __salt__
    ret = {}
    for id_ in _s['mc_pillar.query'](
        'vms', {}
    ).get('lxc', {}):
        if to_file:
            out = os.path.join(export_dir, '0150_bm_{0}.yml'.format(
                id_.split('.')[0]))
        r = export_lxc_compute_node(id_, out_file=out)
        ret[id_] = r
    return ret
# vim:set et sts=4 ts=4 tw=80:
