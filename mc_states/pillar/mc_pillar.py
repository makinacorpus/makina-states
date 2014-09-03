#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
'''
code may seem not very pythonic, this is because at first, this is
a port for a jinja based dynamic pillar
'''

# Import salt libs
import mc_states.utils
import random
import os
import logging
import traceback


log = logging.getLogger(__name__)

__name = 'salt'


def get_global_conf(id_, gconf=None, ms_vars=None):
    if not gconf:
        gconf = __salt__['mc_pillar.get_configuration'](id_)
    return gconf


def slave_key(id_, dnsmaster=None, master=True,  gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    ip_for = __salt__['mc_pillar.ip_for']
    rdata = {}
    oip = ip_for(id_)
    if not master:
        mip = ip_for(dnsmaster)
        # on slave side, declare the master as the tsig
        # key consumer
        rdata[
            'makina-states.services.dns.bind.servers.{0}'.format(
                mip)] = {'keys': [oip]}
    # on both, say to encode with the client tsig key when daemons
    # are talking to each other
    rdata['makina-states.services.dns.bind.keys.{0}'.format(oip)] = {
        'secret': __salt__['mc_bind.tsig_for'](oip)}
    return rdata


def get_makina_states_variables(id_, gconf=None, ms_vars=None):
    if not ms_vars:
        ms_vars = __salt__['mc_pillar.get_makina_states_variables'](id_)
    return ms_vars


def rrs(domain):
    infos = __salt__['mc_pillar.get_nss_for_zone'](domain)
    master = infos['master']
    slaves = infos['slaves']
    allow_transfer = []
    if slaves:
        slaveips = []
        for s in slaves:
            slaveips.append('key "{0}"'.format(
                __salt__['mc_pillar.ip_for'](s)))
        allow_transfer = slaveips
        soans = slaves.keys()[0]
    else:
        soans = master
    rdata = {
        'allow_transfer': allow_transfer,
        'serial': __salt__['mc_pillar.serial_for'](domain),
        'soa_ns': soans,
        'soa_contact': 'postmaster.{0}'.format(domain),
        'rrs': __salt__['mc_pillar.rrs_for'](domain, aslist=True)
    }
    return rdata


def get_dns_master_conf(id_, gconf=None, ms_vars=None):
    rdata = {
        'makina-states.services.dns.bind': True
    }
    altdomains = []
    for domains in __salt__['mc_pillar.query'](
        'managed_alias_zones'
    ).values():
        altdomains.extend(domains)
    for domain in __salt__[
        'mc_pillar.query'](
            'managed_dns_zones'):
        if domain not in altdomains:
            rdata[
                'makina-states.services.dns.bind'
                '.zones.{0}'.format(domain)] = rrs(
                    domain)
    for altdomain in __salt__[
        'mc_pillar.query'](
            'managed_alias_zones').get(domain, []):
        srrs = rrs(domain).replace(domain, altdomain)
        srrs = [a for a in srrs.split('\n')
                if a.strip()]
        rdata['makina-states.services.dns.bind'
              '.zones.{0}'.format(altdomain)] = srrs
    dnsslaves = __salt__[
        'mc_pillar.get_slaves_for'](id_)['all']
    if dnsslaves:
        # slave tsig declaration
        rdata[
            'makina-states.services.dns.bind.slaves'
        ] = [__salt__['mc_pillar.ip_for'](slv)
             for slv in dnsslaves]
        for dn in dnsslaves:
            rdata.update(slave_key(dn))
            rdata[
                'makina-states.services.dns.bind'
                '.servers.{0}'.format(
                    __salt__['mc_pillar.ip_for'](dn)
                )
            ] = {
                'keys': [
                    __salt__['mc_pillar.ip_for'](dn)]
            }
    return rdata


def get_snmpd_conf(id_, gconf=None, ms_vars=None):
    data = __salt__['mc_pillar.get_snmpd_settings'](id_)
    gconf = get_global_conf(id_, gconf)
    rdata = {}
    pref = "makina-states.services.monitoring.snmpd"
    if gconf.get('manage_snmpd', False):
        rdata.update({
            pref: True,
            pref + ".default_user": data['user'],
            pref + ".default_password": data['password'],
            pref + ".default_key": data['key']})
    return rdata


def get_fail2ban_conf(id_, gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    rdata = {}
    pref = "makina-states.services.firewall.fail2ban"
    if gconf.get('manage_snmpd', False):
        rdata.update({
            pref: True,
            pref + ".ignoreip": __salt__['mc_pillar.whitelisted'](id_)})
    return rdata


def get_ntp_server_conf(id_, gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    rdata = {}
    if gconf.get('manage_ntp_server', False):
        rdata.update({
            'makina-states.services.base.ntp.kod': False,
            'makina-states.services.base.ntp.peer': False,
            'makina-states.services.base.ntp.trap': False,
            'makina-states.services.base.ntp.query': False})
    return rdata


def get_ldap_client_conf(id_, gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    rdata = {}
    if gconf.get('ldap_client', False):
        conf = __salt__['mc_pillar.get_ldap_configuration'](id_)
        rdata['makina-states.localsettings.ldap'] = {
            'ldap_uri': conf['ldap_uri'],
            'ldap_base': conf['ldap_base'],
            'ldap_passwd': conf['ldap_passwd'],
            'ldap_shadow': conf['ldap_shadow'],
            'ldap_group': conf['ldap_group'],
            'ldap_cacert': conf['ldap_cacert'],
            'enabled': conf['enabled'],
            'nslcd': {'ssl': conf['nslcd']['ssl']}}
    return rdata


def get_mail_conf(id_, gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    if not gconf.get('manage_mails', False):
        return {}
    data = {}
    mail_conf = __salt__['mc_pillar.get_mail_configuration'](id_)
    dest = mail_conf['default_dest'].format(id=id_)
    data['makina-states.services.mail.postfix'] = True
    data['makina-states.services.mail.postfix.mode'] = mail_conf['mode']
    if mail_conf.get('transports'):
        transports = data.setdefault(
            'makina-states.services.mail.postfix.transport', [])
        for entry, host in mail_conf['transports'].items():
            if entry != '*':
                transports.append({
                    'transport': entry,
                    'nexthop': 'relay:[{0}]'.format(host)})
        if '*' in mail_conf['transports']:
            transports.append(
                {'nexthop':
                 'relay:[{0}]'.format(mail_conf['transports']['*'])})
        if mail_conf['auth']:
            passwds = data.setdefault(
                'makina-states.services.mail.postfix.sasl_passwd', [])
            data['makina-states.services.mail.postfix.auth'] = True
            for entry, host in mail_conf['smtp_auth'].items():
                passwds.append({
                    'entry': '[{0}]'.format(entry),
                    'user': host['user'],
                    'password': host['password']})
        if mail_conf.get('virtual_map'):
            vmap = data.setdefault(
                'makina-states.services.mail.postfix.virtual_map', {})
        for record in mail_conf['virtual_map']:
            for item, val in record.items():
                vmap[item.format(id=id_, dest=dest)] = val.format(
                    id=id_, dest=dest)
    return data


def get_ssh_keys_conf(id_, gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    rdata = {}
    pref = "makina-states.services.base.ssh.server"
    adm_pref = "makina-states.localsettings.admin.sysadmins_keys"
    a_adm_pref = "makina-states.localsettings.admin.absent_keys"
    if gconf.get('manage_ssh_keys', False):
        absent_keys = []
        for k in __salt__['mc_pillar.get_removed_keys'](id_):
            absent_keys.append({k: {}})
        rdata.update({
            adm_pref: __salt__['mc_pillar.get_sysadmins_keys'](id_),
            a_adm_pref: absent_keys,
            pref + ".chroot_sftp": True})
    return rdata


def get_ssh_groups_conf(id_, gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    rdata = {}
    pref = "makina-states.services.base.ssh.server"
    if gconf.get('manage_ssh_groups', False):
        rdata.update({
            pref + ".allowgroups": __salt__['mc_pillar.get_ssh_groups'](id_),
            pref + ".chroot_sftp": True})
    return rdata


def get_sudoers_conf(id_, gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    rdata = {}
    pref = "makina-states.localsettings.admin.sudoers"
    if gconf.get('manage_sudoers', False):
        rdata.update({
            pref: __salt__['mc_pillar.get_sudoers'](id_)})
    return rdata


def get_packages_conf(id_, gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    rdata = {}
    pref = "makina-states.localsettings.pkgs.apt"
    if gconf.get('manage_packages', False):
        rdata.update({
            pref + ".ubuntu.mirror": "http://mirror.ovh.net/ftp.ubuntu.com/",
            pref + ".debian.mirror": (
                "http://mirror.ovh.net/ftp.debian.org/debian/")
        })
    return rdata


def get_default_env_conf(id_, gconf=None, ms_vars=None):
    conf = get_global_conf(id_, gconf)
    rdata = {}
    conf = __salt__['mc_pillar.get_configuration'](id_)
    rdata['default_env'] = conf['default_env']
    return rdata


def get_shorewall_conf(id_, gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    rdata = {}
    if gconf.get('manage_shorewall', False):
        rdata.update(__salt__['mc_pillar.get_shorewall_settings'](id_))
    return rdata


def get_sysnet_conf(id_, gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    ms_vars = get_makina_states_variables(id_, ms_vars=ms_vars)
    rdata = {}
    if ms_vars.get('is_bm', False) and gconf.get('manage_network', False):
        rdata['a'] = 'b'
    return rdata


def get_autoupgrade_conf(id_, gconf=None, ms_vars=None):
    ms_vars = get_makina_states_variables(id_, ms_vars=ms_vars)
    gconf = get_global_conf(id_, gconf)
    rdata = {}
    if ms_vars.get('is_bm', False):
        rdata['makina-states.localsettings.autoupgrade'] = gconf[
            'manage_autoupgrades']
    return rdata


def get_burp_server_conf(id_, gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    rdata = {}
    if __salt__['mc_pillar.is_burp_server'](id_):
        conf = __salt__['mc_pillar.backup_server_settings_for'](id_)
        rdata['makina-states.services.backup.burp.server'] = True
        for host, conf in conf['confs'].items():
            if conf['type'] in ['burp']:
                rdata[
                    'makina-states.services.'
                    'backup.burp.clients.{0}'.format(host)
                ] = conf['conf']
    return rdata


def get_slapd_conf(id_, gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    rdata = {}
    if (
        __salt__['mc_pillar.is_ldap_master'](id_)
        or __salt__['mc_pillar.is_ldap_slave'](id_)
    ):
        data = __salt__['mc_pillar.get_slapd_conf'](id_)
        rdata['makina-states.services.dns.slapd'] = True
        for k in ['tls_cacert', 'tls_cert', 'tls_key',
                  'mode', 'config_pw', 'root_dn', 'dn', 'root_pw']:
            val = data.get(k, None)
            if val:
                rdata[
                    'makina-states.services.dns.slapd.{0}'.format(val)] = val
    return rdata


def get_backup_client_conf(id_, gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    rdata = {}
    if gconf.get('manage_backups', False):
        conf = __salt__['mc_pillar.get_configuration'](id_)
        mode = conf['backup_mode']
        if mode == 'rdiff':
            rdata['makina-states.services.backup.rdiff-backup'] = True
        elif 'burp' in mode:
            rdata['makina-states.services.backup.burp.client'] = True
    return rdata


def get_etc_hosts_conf(id_, gconf=None, ms_vars=None):
    gconf = get_global_conf(id_, gconf)
    rdata = {}
    if gconf.get('manage_hosts', False):
        hosts = __salt__['mc_pillar.query']('hosts').get(id_, [])
        if hosts:
            dhosts = rdata.setdefault('makina-bosts', [])
            for entry in hosts:
                ip = entry.get('ip', __salt__['mc_pillar.ip_for'](id_))
                dhosts.append({'ip': ip, 'hosts': entry['hosts']})
    return rdata


def get_passwords_conf(id_, gconf=None, ms_vars=None):
    '''
    Idea is to have
    - simple users gaining sudoer access
    - powerusers known as sysadmin have:
        - access to sysadmin user via ssh key
        - access to root user via ssh key
    - They are also sudoers with their username (trigramme)
    - ssh accesses are limited though access groups, so we also map here
      the groups which have access to specific machines
    '''
    gconf = get_global_conf(id_, gconf)
    ms_vars = get_makina_states_variables(id_, ms_vars=ms_vars)
    rdata = {}
    pref = "makina-states.localsettings"
    apref = pref + ".admin"
    if gconf.get('manage_passwords', False):
        passwords = __salt__['mc_pillar.get_passwords'](id_)
        for user, password in passwords['crypted'].items():
            if user not in ['root', 'sysadmin']:
                rdata[
                    pref + '.users.{0}.password'.format(
                        user)] = password
        rdata.update({
            apref + ".root_password": passwords['crypted']['root'],
            apref + ".sysadmin_password": passwords['crypted']['sysadmin']})
    return rdata


def ext_pillar(id_, pillar, *args, **kw):
    data = {}
    gconf = get_global_conf(id_)
    ms_vars = get_makina_states_variables(id_)
    for callback in [
        get_autoupgrade_conf,
        get_backup_client_conf,
        get_burp_server_conf,
        get_default_env_conf,
        get_dns_master_conf,
        get_etc_hosts_conf,
        get_fail2ban_conf,
        get_ldap_client_conf,
        get_mail_conf,
        get_ntp_server_conf,
        get_packages_conf,
        get_passwords_conf,
        get_shorewall_conf,
        get_slapd_conf,
        get_snmpd_conf,
        get_ssh_groups_conf,
        get_ssh_keys_conf,
        get_sudoers_conf,
        get_sysnet_conf,
    ]:
        args, kw = (id_,), {'gconf': gconf, 'ms_vars': ms_vars}
        try:
            data = __salt__['mc_utils.dictupdate'](data,
                                                   callback(*args, **kw))
        except Exception, ex:
            trace = traceback.format_exc()
            log.error('ERROR in mc_pillar {0}'.format(callback))
            log.error(ex)
            log.error(trace)
    return data

# vim:set et sts=4 ts=4 tw=80:
