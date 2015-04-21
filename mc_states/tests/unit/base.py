#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import copy
try:
    import unittest2 as unittest
except ImportError:
    import unittest

from salt.modules import grains as sgrains

from mc_states.modules import mc_apache as mmc_apache
from mc_states.modules import mc_autoupgrade as mmc_autoupgrade
from mc_states.modules import mc_bind as mmc_bind
from mc_states.modules import mc_bootstraps as mmc_bootstraps
from mc_states.modules import mc_burp as mmc_burp
from mc_states.modules import mc_casperjs as mmc_casperjs
from mc_states.modules import mc_circus as mmc_circus
from mc_states.modules import mc_cloud as mmc_cloud
from mc_states.modules import mc_cloud_compute_node as mmc_cloud_compute_node
from mc_states.modules import mc_cloud_controller as mmc_cloud_controller
from mc_states.modules import mc_cloud_images as mmc_cloud_images
from mc_states.modules import mc_cloud_kvm as mmc_cloud_kvm
from mc_states.modules import mc_cloud_lxc as mmc_cloud_lxc
from mc_states.modules import mc_cloud_saltify as mmc_cloud_saltify
from mc_states.modules import mc_cloud_vm as mmc_cloud_vm
from mc_states.modules import mc_controllers as mmc_controllers
from mc_states.modules import mc_dbsmartbackup as mmc_dbsmartbackup
from mc_states.modules import mc_dhcpd as mmc_dhcpd
from mc_states.modules import mc_dns as mmc_dns
from mc_states.modules import mc_dumper as mmc_dumper
from mc_states.modules import mc_env as mmc_env
from mc_states.modules import mc_etckeeper as mmc_etckeeper
from mc_states.modules import mc_etherpad as mmc_etherpad
from mc_states.modules import mc_fail2ban as mmc_fail2ban
from mc_states.modules import mc_grub as mmc_grub
from mc_states.modules import mc_haproxy as mmc_haproxy
from mc_states.modules import mc_icinga2 as mmc_icinga2
from mc_states.modules import mc_icinga as mmc_icinga
from mc_states.modules import mc_icinga_web as mmc_icinga_web
from mc_states.modules import mc_java as mmc_java
from mc_states.modules import mc_kernel as mmc_kernel
from mc_states.modules import mc_ldap as mmc_ldap
from mc_states.modules import mc_locales as mmc_locales
from mc_states.modules import mc_localsettings as mmc_localsettings
from mc_states.modules import mc_locations as mmc_locations
from mc_states.modules import mc_logrotate as mmc_logrotate
from mc_states.modules import mc_lxc as mmc_lxc
from mc_states.modules import mc_macros as mmc_macros
from mc_states.modules import mc_memcached as mmc_memcached
from mc_states.modules import mc_mongodb as mmc_mongodb
from mc_states.modules import mc_monitoring as mmc_monitoring
from mc_states.modules import mc_mumble as mmc_mumble
from mc_states.modules import mc_mysql as mmc_mysql
from mc_states.modules import mc_nagvis as mmc_nagvis
from mc_states.modules import mc_network as mmc_network
from mc_states.modules import mc_nginx as mmc_nginx
from mc_states.modules import mc_nodejs as mmc_nodejs
from mc_states.modules import mc_nodetypes as mmc_nodetypes
from mc_states.modules import mc_nscd as mmc_nscd
from mc_states.modules import mc_ntp as mmc_ntp
from mc_states.modules import mc_pgsql as mmc_pgsql
from mc_states.modules import mc_phantomjs as mmc_phantomjs
from mc_states.modules import mc_php as mmc_php
from mc_states.modules import mc_pillar as mmc_pillar
from mc_states.modules import mc_pkgs as mmc_pkgs
from mc_states.modules import mc_pnp4nagios as mmc_pnp4nagios
from mc_states.modules import mc_postfix as mmc_postfix
from mc_states.modules import mc_project_1 as mmc_project_1
from mc_states.modules import mc_project_2 as mmc_project_2
from mc_states.modules import mc_project as mmc_project
from mc_states.modules import mc_provider as mmc_provider
from mc_states.modules import mc_psad as mmc_psad
from mc_states.modules import mc_pureftpd as mmc_pureftpd
from mc_states.modules import mc_rabbitmq as mmc_rabbitmq
from mc_states.modules import mc_rdiffbackup as mmc_rdiffbackup
from mc_states.modules import mc_redis as mmc_redis
from mc_states.modules import mc_remote as mmc_remote
from mc_states.modules import mc_rsyslog as mmc_rsyslog
from mc_states.modules import mc_rvm as mmc_rvm
from mc_states.modules import mc_salt as mmc_salt
from mc_states.modules import mc_screen as mmc_screen
from mc_states.modules import mc_services as mmc_services
from mc_states.modules import mc_shorewall as mmc_shorewall
from mc_states.modules import mc_slapd as mmc_slapd
from mc_states.modules import mc_snmpd as mmc_snmpd
from mc_states.modules import mc_ssh as mmc_ssh
from mc_states.modules import mc_ssl as mmc_ssl
from mc_states.modules import mc_state as mmc_state
from mc_states.modules import mc_supervisor as mmc_supervisor
from mc_states.modules import mc_timezone as mmc_timezone
from mc_states.modules import mc_tomcat as mmc_tomcat
from mc_states.modules import mc_ubuntugis as mmc_ubuntugis
from mc_states.modules import mc_ulogd as mmc_ulogd
from mc_states.modules import mc_updatedb as mmc_updatedb
from mc_states.modules import mc_usergroup as mmc_usergroup
from mc_states.modules import mc_utils as mmc_utils
from mc_states.modules import mc_uwsgi as mmc_uwsgi
from mc_states.modules import mc_www as mmc_www    

from mc_states.states import mc_apache as smc_apache
from mc_states.states import mc_git as smc_git
from mc_states.states import mc_lxc as smc_lxc
from mc_states.states import mc_php as smc_php
from mc_states.states import mc_postgres_database as smc_postgres_database
from mc_states.states import mc_postgres_extension as smc_postgres_extension
from mc_states.states import mc_postgres_group as smc_postgres_group
from mc_states.states import mc_postgres_user as smc_postgres_user
from mc_states.states import mc_project as smc_project
from mc_states.states import mc_proxy as smc_proxy
from mc_states.states import mc_registry as smc_registry

from mc_states.renderers import lyaml as rmc_lyaml

from mc_states.pillar import mc_pillar as pmc_pillar

import mc_states.tests.utils

J = os.path.join
D = os.path.dirname
STATES_DIR = J(D(D(D(__file__))), '_modules')
_NO_ATTR = object()
DUNDERS = {
    'default': {
        'opts': {
            'config_dir': '/etc/mastersalt',
            'extension_modules': '/var/cache/salt/salt-minion/extmods',
            'renderer': 'yaml_jinja',
        },
        'salt': {},
        'pillar': {},
        'grains': {},
        'context': {}}}
DUNDERS['modules'] = copy.deepcopy(DUNDERS['default'])
DUNDERS['modules']['salt'] = {
    'lyaml.render': rmc_lyaml.render,
    'mc_remote.sls': mmc_remote.sls_,
    'mc_remote.highstate': mmc_remote.highstate,
    'mc_remote.salt_call': mmc_remote.salt_call,
    'mc_remote.mastersalt_call': mmc_remote.mastersalt_call,
    'mc_remote.ssh': mmc_remote.ssh,
    'mc_remote.ssh_transfer_file': mmc_remote.ssh_transfer_file,
    'mc_remote.ssh_transfer_dir': mmc_remote.ssh_transfer_dir,
    'grains.filter_by': sgrains.filter_by,
    'mc_ntp.settings': mmc_ntp.settings,
    'mc_locations.settings': mmc_locations.settings,
    'mc_dumper.sanitize_kw': mmc_dumper.sanitize_kw,
    'mc_dumper.yencode': mmc_dumper.yencode,
    'mc_dumper.cyaml_load': mmc_dumper.cyaml_load,
    'mc_dumper.yaml_load': mmc_dumper.yaml_load,
    'mc_dumper.yaml_dump': mmc_dumper.yaml_dump,
    'mc_dumper.cyaml_dump': mmc_dumper.cyaml_dump,
    'mc_dumper.old_yaml_dump': mmc_dumper.old_yaml_dump,
    'mc_dumper.iyaml_dump': mmc_dumper.iyaml_dump,
    'mc_dumper.msgpack_load': mmc_dumper.msgpack_load,
    'mc_dumper.msgpack_dump': mmc_dumper.msgpack_dump,
    'mc_dumper.json_load': mmc_dumper.json_load,
    'mc_dumper.json_dump': mmc_dumper.json_dump,
    'mc_localsettings.get_pillar_sw_ip':
    mmc_localsettings.get_pillar_sw_ip,
    'mc_pillar.get_sysadmins_keys':
    mmc_pillar.get_sysadmins_keys,
    'mc_pillar.ip_for': mmc_pillar.ip_for,
    'mc_pillar.ips_for': mmc_pillar.ips_for,
    'mc_utils.yaml_dump':
    mmc_utils.yaml_dump,
    'mc_utils.yaml_load':
    mmc_utils.yaml_load,
    'mc_utils.msgpack_dump':
    mmc_utils.msgpack_dump,
    'mc_utils.msgpack_load':
    mmc_utils.msgpack_load,
    'mc_macros.yaml_load_local_registry':
    mmc_macros.yaml_load_local_registry,
    'mc_macros.yaml_load_local_registry':
    mmc_macros.yaml_load_local_registry,
    'mc_macros.yaml_dump_local_registry':
    mmc_macros.yaml_dump_local_registry,
    'mc_macros.pack_load_local_registry':
    mmc_macros.pack_load_local_registry,
    'mc_macros.pack_dump_local_registry':
    mmc_macros.pack_dump_local_registry,
    'mc_macros.get_local_registry':
    mmc_macros.get_local_registry,
    'mc_macros.update_local_registry':
    mmc_macros.update_local_registry,
    'mc_pillar.load_db': mmc_pillar.load_db,
    'mc_pillar.query': mmc_pillar.query,
    'mc_pillar.whitelisted': mmc_pillar.whitelisted,
    'mc_utils.local_minion_id': mmc_utils.local_minion_id,
    'mc_utils.format_resolve': mmc_utils.format_resolve,
    'mc_utils.defaults': mmc_utils.defaults,
    'mc_utils.magicstring': mmc_utils.magicstring,
    'mc_utils.get': mmc_utils.get,
    'mc_utils.dictupdate': mmc_utils.dictupdate,
    'mc_utils.uniquify': mmc_utils.uniquify,
    'mc_utils.unix_crypt': mmc_utils.unix_crypt,
    'mc_utils.invalidate_memoize_cache': mmc_utils.invalidate_memoize_cache,
    'mc_utils.generate_password': mmc_utils.generate_password,
    'mc_utils.memoize_cache': mmc_utils.memoize_cache}


class ModuleCase(unittest.TestCase):
    '''Base test class
    Its main function is to be used in salt modules
    and to mock the __salt__, __pillar__ and __grains__ attributes
    all in one place

    '''
    _mods = tuple()
    maxDiff = None
    _to_patch = ('salt', 'pillar', 'grains', 'opts', 'context')
    kind = 'modules'

    def reset_dunders(self):
        self.dunders = copy.deepcopy(DUNDERS)

    def setUp(self):
        '''
        1. Monkey patch the dunders (__salt__, __grains__ & __pillar__; etc)
        in the objects (certainly python modules) given in self.mods

            - This search in self._{grains, pillar, salt} for a dict containing
              the monkey patch replacement and defaults to {}
            - We will then have on the test class _salt, _grains & _pillar
              dicts to be used and mocked in tests, this ensure that the mock
              has to be done only at one place, on the class attribute.

        '''
        mc_states.tests.utils.test_setup()
        self.reset_dunders()
        for patched in self._to_patch:
            patch = self.dunders[self.kind].setdefault(patched, {})
            setattr(self, '_{0}'.format(patched), patch)
            for mod in self._mods:
                sav_attribute = '___mc_patch_{0}'.format(patched)
                attribute = '__{0}__'.format(patched)
                if hasattr(mod, sav_attribute):
                    raise ValueError('test conflict')
                if not hasattr(mod, sav_attribute):
                    setattr(mod, sav_attribute,
                            getattr(mod, attribute, _NO_ATTR))
                    setattr(mod, attribute, patch)

    def tearDown(self):
        '''
        1. Ungister any Monkey patch on  __salt__, __grains__ & __pillar__ in
        objects (certainly python modules) given in self.mods
        '''
        for mod in self._mods:
            for patched in self._to_patch:
                attribute = '__{0}__'.format(patched)
                sav_attribute = '___mc_patch_{0}'.format(patched)
                _patch = getattr(mod, sav_attribute, None)
                if _patch is not None:
                    if _patch is not _NO_ATTR:
                        setattr(mod, attribute, _patch)
                    else:
                        delattr(mod, attribute)
                    delattr(mod, sav_attribute)
                shortcut = '_{0}'.format(patched)
                if hasattr(self, shortcut):
                    delattr(self, shortcut)
        self.reset_dunders()
        mc_states.tests.utils.test_teardown()
# vim:set et sts=4 ts=4 tw=80:
