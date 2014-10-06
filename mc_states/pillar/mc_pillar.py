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
import re
import os
import logging
import traceback
import cProfile, pstats


log = logging.getLogger(__name__)
__name = 'salt'


def ext_pillar(id_, pillar, *args, **kw):
    try:
        profile_enabled = kw.get('profile', False)
    except:
        profile_enabled = False
    data = {}
    if profile_enabled:
        pr = cProfile.Profile()
        pr.enable()
    for callback in [
        'mc_pillar.get_dns_resolvers',
        'mc_pillar.get_custom_pillar_conf',
        'mc_pillar.get_autoupgrade_conf',
        'mc_pillar.get_backup_client_conf',
        'mc_pillar.get_burp_server_conf',
        'mc_pillar.get_cloudmaster_conf',
        'mc_pillar.get_default_env_conf',
        'mc_pillar.get_dhcpd_conf',
        'mc_pillar.get_dns_master_conf',
        'mc_pillar.get_dns_slave_conf',
        'mc_pillar.get_etc_hosts_conf',
        'mc_pillar.get_fail2ban_conf',
        'mc_pillar.get_ldap_client_conf',
        'mc_pillar.get_mail_conf',
        'mc_pillar.get_ntp_server_conf',
        'mc_pillar.get_packages_conf',
        'mc_pillar.get_passwords_conf',
        'mc_pillar.get_shorewall_conf',
        'mc_pillar.get_slapd_pillar_conf',
        'mc_pillar.get_snmpd_conf',
        'mc_pillar.get_supervision_client_conf',
        'mc_pillar.get_ssh_groups_conf',
        'mc_pillar.get_ssh_keys_conf',
        'mc_pillar.get_sudoers_conf',
        'mc_pillar.get_supervision_confs',
        'mc_pillar.get_sysnet_conf',
    ]:
        try:
            data = __salt__['mc_utils.dictupdate'](
                data, __salt__[callback](id_))
        except Exception, ex:
            trace = traceback.format_exc()
            log.error('ERROR in mc_pillar: {0}'.format(callback))
            log.error(ex)
            log.error(trace)
    if profile_enabled:
        pr.disable()
        if not os.path.isdir('/tmp/stats'):
            os.makedirs('/tmp/stats')
        ficp = '/tmp/stats/{0}.pstats'.format(id_)
        fico = '/tmp/stats/{0}.dot'.format(id_)
        ficn = '/tmp/stats/{0}.stats'.format(id_)
        os.system(
            '/srv/mastersalt/makina-states/bin/pyprof2calltree '
            '-i {0} -o {1}'.format(ficp, fico))
        if not os.path.exists(ficp):
            pr.dump_stats(ficp)
            with open(ficn, 'w') as fic:
                ps = pstats.Stats(
                    pr, stream=fic).sort_stats('cumulative')
                ps.print_stats()
    return data

# vim:set et sts=4 ts=4 tw=80:
