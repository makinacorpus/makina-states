# -*- coding: utf-8 -*-
'''
.. _module_mc_bind:

mc_bind / named/bind functions
============================================
For the documentation on usage, please look :ref:`bind_documentation`.
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import mc_states.utils
from copy import deepcopy

from salt.utils.odict import OrderedDict

__name = 'bind'

log = logging.getLogger(__name__)


def settings():
    '''
    Named settings

    WARNING: THIS FOR NOW JUST TAKE IN ACCOUNT SETTINGS ABOUT
    A CACHING DNS SERVER, THE ZONE MANAGMENT HAS BEEN
    ABANDONNED IN FAVOR OF POWERDNS

    For the documentation on usage, please look :ref:`bind_documentation`.

        pkgs
            pkg to install for a named install
        config
            primary config file path
        local_config
            local primary config file path
        options_config'
            options config file path
        default_zones_config
            default zone config file path
        dnssec
            do we use dnssec (not implemented now)
        named_directory
            var directory
        user
            user for named service (root)
        group
            group for named service (named)
        service_name
            service name
        mode
            configuration files mode ('640')
        zones
            zones
        rzones
            reverse zones
        secondary_zones
            secondary zones
        secondary_rzones
            secondary reverse zones
        serial
            2014030501
        ttl
            3600,
        refresh
            3600
        retry
            300
        expire
            2419200
        minimum
            3600
        rndc_conf
            path to rndc configuration
        rndc_key
            path to rndc key
        servers_config_template
            salt://makina-states/files/etc/bind/named.conf.servers
        key_config_template
            {{settingsnsalt://makina-states/files/etc/bind/named.conf.key
        bind_config_template
            salt://makina-states/files/etc/bind/named.conf
        local_config_template
           salt://makina-states/files/etc/bind/named.conf.local
        options_config_template
           salt://makina-states/files/etc/bind/named.conf.options'
        logging_zones_config_template
           salt://makina-states/files/etc/bind/named.conf.logging
        default_zones_config_template
           salt://makina-states/files/etc/bind/named.conf.default-zones
        zone_template
           salt://makina-states/files/etc/bind/pri_zone.zone
        sec_reverse_template
           salt://makina-states/files/etc/bind/sec_reverse.zone
        sec_zone_template
           salt://makina-states/files/etc/bind/sec_zone.zone
        reverse_template
           salt://makina-states/files/etc/bind/pri_reverse.zone
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        os_defaults = __salt__['grains.filter_by']({
            'Debian': {
                'pkgs': ['bind9',
                         'bind9utils',
                         'bind9-host'],
                'config_dir': '/etc/bind',
                'bind_config': '/etc/bind/named.conf',
                'acl_config': '/etc/bind/named.conf.acl',
                'views_config': '/etc/bind/named.conf.views',
                'servers_config': (
                    '/etc/bind/named.conf.servers'),
                'logging_config': '/etc/bind/named.conf.logging',
                'local_config': '/etc/bind/named.conf.local',
                'options_config': '/etc/bind/named.conf.options',
                'key_config': '/etc/bind/named.conf.key',
                'default_zones_config': (
                    '/etc/bind/named.conf.default-zones'),
                'cache_directory': '/var/cache/bind',
                'named_directory': '/var/cache/bind/zones',
                'dnssec': True,
                'user': 'root',
                'group': 'bind',
                'service_name': 'bind9',
            },
            'RedHat': {
                'pkgs': ['bind'],
                'config_dir': '/etc',
                'bind_config': '/etc/named.conf',
                'local_config': '/etc/named.conf.local',
                'cache_directory': '/var/named',
                'named_directory': '/var/named/data',
                'user': 'root',
                'group': 'named',
                'service_name': 'named',
            },
        },
            grain='os_family', default='Debian')
        defaults = __salt__['mc_utils.dictupdate'](
            os_defaults, {
                'default_dnses': ['8.8.8.8', '4.4.4.4'],
                'log_dir': '/var/log/named',
                "rndc_conf": "/etc/rndc.conf",
                "rndc_key": "/etc/bind/rndc.key",
                'default_view': 'net',
                'ipv4': 'any',
                'ipv6': 'any',
                'mode': '640',
                'view_defaults': {
                    'match_clients': ['any'],
                    'recursion': 'no',
                    'additional_from_auth': 'no',
                    'additional_from_cache': 'no',
                },
                'serial': '2014030501',
                'ttl': '3600',
                'refresh': '3600',
                'retry': '300',
                'expire': '2419200',
                'minimum': '3600',
                'bind_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf'
                ),
                'servers_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.servers'
                ),
                'views_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.views'
                ),
                'acl_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.acl'
                ),
                'logging_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.logging'
                ),
                'key_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.key'
                ),
                'local_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.local'
                ),
                'options_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.options'
                ),
                'default_zones_config_template': (
                    'salt://makina-states/files/'
                    'etc/bind/named.conf.default-zones'
                ),
                'rndc_config_template': (
                    'salt://makina-states/files/'
                    'etc/rndc.conf'
                ),
                'zone_template': (
                    'salt://makina-states/files/'
                    'etc/bind/pri_zone.zone'),
                'sec_reverse_template': (
                    'salt://makina-states/files/'
                    'etc/bind/sec_reverse.zone'),
                'sec_zone_template': (
                    'salt://makina-states/files/'
                    'etc/bind/sec_zone.zone'),
                'reverse_template': (
                    'salt://makina-states/files/'
                    'etc/bind/pri_reverse.zone'),
                #
                'keys': OrderedDict(),
                'servers': OrderedDict(),
                'views': OrderedDict(),
                'acls': OrderedDict(),
                'zones': OrderedDict(),
                'rzones': OrderedDict(),
                'secondary_zones': OrderedDict(),
                'secondary_rzones': OrderedDict(),
            }
        )
        defaults['extra_dirs'] = [
            '{0}/reverses/primary'.format(
                defaults['config_dir']),
            '{0}/reverses/secondary'.format(
                defaults['config_dir']),
            '{0}/zones/primary'.format(
                defaults['config_dir']),
            '{0}/zones/secondary'.format(
                defaults['config_dir']),
        ]
        defaults['zone_kinds'] = {
            'secondary_zones': {
                'server_type': 'secondary',
                'zone_type': 'zone',
                'source': defaults['sec_zone_template'],
            },
            'secondary_rzones': {
                'server_type': 'secondary',
                'zone_type': 'reverse',
                'source': defaults['sec_reverse_template'],
            },
            'zones': {
                'server_type': 'primary',
                'zone_type': 'zone',
                'source': defaults['zone_template'],
            },
            'rzones': {
                'server_type': 'primary',
                'zone_type': 'reverse',
                'source': defaults['reverse_template'],
            },
        }
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.dns.bind', defaults)
        #zone_kinds = data['zone_kinds']
        #for k in [a for a in data['servers']]:
        #    adata = data['servers'][k]
        #    adata.setdefault('keys', [])
        #for k in [a for a in data['acls']]:
        #    adata = data['acls'][k]
        #    adata.setdefault('clients', 'any')
        #for k in [a for a in data['keys']]:
        #    kdata = data['keys'][k]
        #    kdata.setdefault('algorithm', 'hmac-md5')
        #    if not 'secret' in kdata:
        #        raise ValueError(
        #            'no secret for {0}'.format(k))
        #for zonekind, metadatas in zone_kinds.items():
        #    for zone in [a for a in data[zonekind]]:
        #        zdata = data[zonekind][zone]
        #        _update_default_data(zone,
        #                             zdata,
        #                             metadatas,
        #                             data)
        #        if not is_valid_zone(zdata):
        #            log.error(
        #                '{0} is an invalid zone'.format(
        #                    zone))
        #            del data[zonekind][zdata]
        #            continue
        #        for view in zdata['views']:
        #            if not view in data['views']:
        #                data['views'][view] = OrderedDict()
        #            vdata = data['views'][view]
        #            vdata['has_zones'] = True
        #for view in [a for a in data['views']]:
        #    vdata = data['views'][view]
        #    for k, v in data['view_defaults'].items():
        #        vdata.setdefault(k, deepcopy(v))
        return data
    return _settings()


def is_valid_zone(data):
    '''A valid zone has:

        - multiples RRs
        - At least one NS and one RR record
    '''

    ret = False
    if data:
        ret = True
    return ret


def _generate_rndc():
    data = ''
    return data


def _update_default_data(zone,
                         zdata,
                         metadatas,
                         defaults):
    zdata.setdefault('views', [])
    single_view = zdata.get('view',
                            defaults['default_view'])
    if (
        single_view
        and not zdata['views']
        and not single_view in zdata['views']
    ):
        zdata['views'].append(single_view)
    zdata.setdefault('rrs', [])
    zdata.setdefault('name', deepcopy(zone))
    zdata.setdefault('template', True)
    for i in [
        'ttl',
        'serial',
        'refresh',
        'retry',
        'expire',
        'minimum'
    ]:
        zdata.setdefault(i, deepcopy(defaults[i]))
    for i in metadatas:
        zdata.setdefault(i, deepcopy(metadatas[i]))
    if zdata['server_type'] == 'primary':
        zdata.setdefault('notify',  True)
    zdata.setdefault('secondaries', [])
    if zdata['server_type'] == 'secondary':
        zdata.setdefault('notify', False)
        if zdata['template']:
            if not 'masters' in zdata:
                raise ValueError(
                    'no masters for {0}'.format(zone)
                )
        zdata.setdefault('masters', [])
    zdata.setdefault(
        'fpath',
        '{3}/{0}s/{1}/{2}.conf'.format(
            zdata['zone_type'],
            zdata['server_type'][:3],
            zdata['name'],
            defaults['config_dir']
        )
    )


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
