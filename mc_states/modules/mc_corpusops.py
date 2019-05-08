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
from salt.utils import yamldumper
from cStringIO import StringIO
from salt.utils.odict import OrderedDict
re_flags = re.M | re.U | re.S
log = logging.getLogger(__name__)
cops_regs_fw_pref = (
    'corpusops_ms_iptables_registrations_registrations_makinastates')
providerre = re.compile('(ovh|online|sys)-')


def cops_inv(lxc=False):
    DEFAULT_COPS_INV = '''
---
{provider_}:
  hosts:
    {id_}: {{}}
'''
    if lxc:
        DEFAULT_COPS_INV += '''compute_nodes_lxcs_makinastates:
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
  vars:
    lxc_compute_node: {id_}
  hosts:
    {id_}:
{id_}_lxcs_makinastates:
  vars: {{}}
  hosts: {{}}
'''
    DEFAULT_COPS_INV += '''
all:
  hosts:
    {id_}: {{}}
'''
    return DEFAULT_COPS_INV


def export_lxc_compute_node(cfg, id_):
    _s = __salt__  # noqa
    db = _s['mc_pillar.get_db_infrastructure_maps']()  # noqa
    cnconf = _s['mc_pillar.get_cloud_entry_for_cn'](id_)
    lxcmak = cfg[id_+'_lxcs_makinastates']
    for vm in cnconf['vms']:
        vmdata = lxcmak['hosts'].setdefault(vm, OrderedDict())
        domains = _s['mc_pillar.query'](
            'cloud_vm_attrs', {}).get(vm, {}).get('domains', [])
        vmconf = _s['mc_pillar.get_cloud_conf_for_vm'](vm)
        np = vmconf.get('network_profile', {})
        if vm not in domains:
            domains.insert(0, vm)
        if domains:
            vmdata['haproxy_hosts'] = domains
        vmdata['ssh_port'] = _s['mc_cloud_compute_node.get_kind_port'](
            vm, target=id_, kind='ssh')
        vmdata['eth0_link'] = 'lxcbr1'
        vmdata['eth0_mac'] = _s['mc_cloud_compute_node.find_mac_for_vm'](
            vm, target=id_)
        vmdata['local_ip'] = _s['mc_cloud_compute_node.get_ip_for_vm'](
            vm, target=id_)
        for ethx in [
            "eth1", "eth2", "eth3", "eth4", "eth5",
            "eth6", "eth7", "eth8", "eth9"
        ]:
            ethxd = np.get(ethx, {})
            if ethxd:
                vmdata['{0}_ip'.format(ethx)] = ethxd.get(
                    'ip',
                    _s['mc_pillar.ips_for'](vm)[0])
                vmdata['{0}_mac'.format(ethx)] = ethxd.get(
                    'hwaddr', ethxd.get('mac', None))
                vmdata['{0}_link'.format(ethx)] = ethxd['link']


def remove_dict_attrs(d, attrs):
    for k in [a for a in d]:
        if isinstance(d[k], dict):
            remove_dict_attrs(d[k], attrs)
        else:
            if k in attrs:
                d.pop(k, None)
    return d


def export_compute_node(id_, out_file=None, lxc=False):
    '''Generate corpusops inventory slug to paste
    inside corpusops compatible inventoy'''
    _s = __salt__  # noqa
    db = _s['mc_pillar.get_db_infrastructure_maps']()  # noqa
    msiptables = _s['mc_pillar.get_ms_iptables_conf'](id_)
    providersrm = providerre.search(id_)
    provider = (not providersrm) and 'ovh' or providersrm.groups()[0]
    cfg = _s['mc_utils.cyaml_load'](
        cops_inv(lxc=lxc).format(id_=id_, provider_=provider))
    rules = msiptables.get(
        'makina-states.services.firewall.ms_iptables.config', {}
    ).get('rules', [])
    if rules:
        cfg['compute_nodes_lxcs_makinastates'][
            'hosts'
        ][id_].setdefault(cops_regs_fw_pref, {})['rules'] = rules
    else:
        if lxc:
            cfg['compute_nodes_lxcs_makinastates']['hosts'][id_] = None
    if lxc:
        export_lxc_compute_node(cfg, id_)
    tips = _s['mc_pillar.ips_for'](id_, fail_over=True)
    if tips:
        ip = tips.pop(0)
        tips.insert(0, '{{public_ip}}')
        cfg['all']['hosts'][id_]['ansible_host'] = ip
        cfg['all']['hosts'][id_]['public_ip'] = ip
        if lxc:
            hvars = cfg['{}_and_lxcs'.format(id_)].setdefault('vars', {})
            hvars['public_ips'] = tips
            hvars['public_ip'] = ip
    if out_file and os.path.exists(out_file):
        with open(out_file) as fic:
            content = fic.read()
        yaml = _y.YAML()
        ncfg = yaml.load(content)
        yaml.preserve_quotes = True
        yaml.explicit_start = True
        yaml.default_flow_style = False
        ncfg = _s['mc_utils.dictupdate'](ncfg, cfg)
        remove_dict_attrs(ncfg, ['ssh_bastion'])
        s = StringIO()
        yaml.dump(ncfg, s)
        dcfg = s.getvalue()
    else:
        dcfg = _s['mc_dumper.yaml_dump'](cfg, flow=False)
    dcfg = re.sub(': null$', ':', dcfg, flags=re_flags)
    dcfg = dcfg.replace('\n    ssh_bastion', ' {ssh_bastion')
    dcfg = dcfg.replace('burpclientserver_profiles_vm\']}\n',
                        'burpclientserver_profiles_vm\']}}\n')
    dcfg = re.sub('(: {ssh_bastion[^}]+)}.$', '\\1}', dcfg, flags=re_flags)
    dcfg = dcfg.replace("ansible_host: '{{public_ip}}'",
                        "ansible_host: \"{{public_ip}}\"")
    if out_file:
        with open(out_file, 'w') as fic:
            fic.write(dcfg)
    return dcfg


def export_makinastates(export_dir='/tmp', to_file=False):
    out = None
    _s = __salt__  # noqa
    ret = {}
    for id_ in _s['mc_pillar.query'](
        'vms', {}
    ).get('lxc', {}):
        if to_file:
            out = os.path.join(export_dir, '0150_bm_{0}.yml'.format(
                id_.split('.')[0]))
        r = export_compute_node(id_, out_file=out, lxc=True)
        ret[id_] = r
    standalone_servers = _s['mc_pillar.query']('backup_servers', {})
    for id_ in standalone_servers:
        if to_file:
            out = os.path.join(export_dir, '0150_bm_{0}.yml'.format(
                id_.split('.')[0]))
        r = export_compute_node(id_, out_file=out, lxc=False)
        ret[id_] = r
    return ret


EXPORT_CMD = '''
ANSIBLE_FORCE_COLOR= ANSIBLE_NOCOLOR=1 ANSIBLE_STDOUT_CALLBACK=json \
    $COPS_ROOT/bin/ansible-playbook -i {inv} -l localhost \
        $COPS_ROOT/roles/corpusops.roles/export/role.yml'''


class AnsibleError(Exception):
    pass


def get_ansible_inventory(item=None,
                          inv='/etc/ansible/inventory',
                          mode=None):
    _s = __salt__  # noqa
    export_mode = {
        'host': 'export_host',
        'group': 'export_group',
    }.get(mode, '')
    cmd = EXPORT_CMD.format(inv=inv)
    if item and export_mode:
        cmd += " -e {0}={1}".format(export_mode, item)
    ret = _s['cmd.run_all'](cmd, python_shell=True)
    if ret['retcode'] != 0:
        print(cmd)
        print(ret['stdout'])
        print(ret['stderr'])
        raise AnsibleError('invalid ansible return')
    aret = _s['mc_dumper.json_load'](ret['stdout'])
    rets = aret['plays'][0]['tasks'][-1]['hosts']
    val = rets[[a for a in rets][0]]
    if not isinstance(val['msg'], dict):
        raise AnsibleError('invalid ansible return type')
    for k in 'groups', 'vars':
        val['msg']['d{0}'.format(k)] = val['msg'][k]
        if isinstance(val['msg'][k], dict):
            continue
        val['msg']['d{0}'.format(k)] = _s['mc_dumper.json_load'](val['msg'][k])
    return val['msg']


def refresh_backup_monit(groups="backup",
                         inv='/etc/ansible/inventory',
                         burp_server_group_key='burp_server_group',
                         to_file=None):
    _s = __salt__  # noqa
    lgroups = groups.split(',')
    arets = {}
    arets['full'] = get_ansible_inventory(inv=inv)
    for g in lgroups:
        arets[g] = get_ansible_inventory(g, inv=inv, mode='group')
    ret = {}
    conf = _s['mc_pillar.query'](
        'supervision_configurations', {}
    ).get('definitions', {}).get('autoconfigured_hosts', {})
    for g in lgroups:
        backuped_hosts = sorted([a for a in arets[g]['dgroups'][g]])
        gserver = arets[g]['vars'][burp_server_group_key]
        bserver = arets['full']['dgroups'][gserver][0]
        for h in backuped_hosts:
            monit = conf.setdefault(h, OrderedDict())
            sattrs = monit.setdefault('services_attrs', OrderedDict())
            ba = sattrs.setdefault('backup_burp_age', OrderedDict())
            ba.setdefault('vars.ssh_port', 22)
            ba.setdefault('vars.data_dir', '/data/burp2')
            ba.setdefault('vars.ssh_host', bserver)
    if to_file:
        econf = {
            'supervision_configurations': {
                'definitions': {
                    'autoconfigured_hosts': conf}}}
        dcfg = _s['mc_dumper.yaml_dump'](econf)
        with open(to_file, 'w') as fic:
            fic.write(dcfg)
            print('exported: {0}'.format(to_file))
    return conf

# vim:set et sts=4 ts=4 tw=80:
