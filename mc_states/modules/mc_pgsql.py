#!/usr/bin/env python

'''

.. _module_mc_pgsql:

mc_pgsql / Postgresql related functions
=======================================
'''
# -*- coding: utf-8 -*-
import re
import os
import copy
from salt.utils.odict import OrderedDict
from salt.utils import context
from copy import deepcopy
from distutils.version import LooseVersion

import mc_states.api


__name = 'pgsql'

PORT_RE = re.compile('port\s*=\s*([0-9]+)[^0-9]*$', re.M | re.U | re.S)
SOCKET_RE = re.compile(
    'unix_socket_director(y|ies)\s*=\s*["\']([^"\']+)["\'].*$',
    re.M | re.U | re.S)
__name = 'postgresql'
PREFIX = 'makina-states.services.db.{0}'.format(__name)


def wrapper(wrappy):
    '''Wrap a postgresql salt module function to set automaticly the socket or port to use.
    This is debian specific for now'''
    def wfunc(name, *args, **kw):
        globs = dict([(k, v) for k, v in globals().items()
                      if not k in ['wrapper', 'args', 'kw',
                                   'PORT_RE', 'SOCKET_RE', 'os', 're']])
        pg_version = kw.get('pg_version', None)
        db_host = kw.get('db_host', None)
        db_port = kw.get('db_port', None)
        if pg_version is not None and db_host is None and db_port is None:
            #
            # Try to link a specific postgres version to a running postgresl
            # socket
            #
            # get info from running postgres with netstat
            pgconf = __salt__['cmd.run_all'](
                'find /etc/postgresql/{0} -name postgresql.conf'
                '|head -n1'.format(
                    pg_version),
                python_shell=True)['stdout']
            if os.path.exists(pgconf):
                with open(pgconf) as fic:
                    content = fic.read().splitlines()
                    socket_dir = None
                    for line in content:
                        if line.startswith('port'):
                            port = PORT_RE.sub('\\1', line)
                        if line.startswith('unix_socket_director'):
                            socket_dir = SOCKET_RE.sub('\\2', line)
                    if port and socket_dir:
                        socket = '{0}/.s.PGSQL.{1}'.format(socket_dir, port)
                        if os.path.exists(socket):
                            db_host = socket_dir
                            db_port = port
            kw.update({'db_host': db_host, 'db_port': db_port})
            del kw['pg_version']
        ret = None
        # inject salt globals in state execution module, stolen from
        # salt.state.py
        with context.func_globals_inject(wrappy, **globs):
            ret = wrappy(name, *args, **kw)
        return ret
    return wfunc


def settings():
    '''
    Postgresql settings registry

    pgDbs
        mapping of postgresql databases with their settings
    postgresqlUsers
        mapping of postgresql users with their settings
    user
        system user
    version
        default postgres version
    defaultPgVersion
        default postgres version
    versions
        activated postgresql version
    postgis
        mapping of supported postgres per postgis version
    postgis_db
        name of the postis template
    pg_hba
        List of pg_hba entries
    pg_conf
        settings for postgresql.conf
        'default' is looked up by default but
        you can override settings for a specific version
        inside a subversion part eg::

            makina-states.services.db.postgresql.pg_conf.9.1:
                port: 5433


            listen
                list of hosts to listen on
            port
                value for port
            unix_socket_directories
                value for unix_socket_directories
            extras
                free dict with key/values pairs,
                for strings you must quote them::

                    makina-states.services.db.postgresql.pg_conf.extras:
                      # no quote
                      enable_tidscan: 'on'
                      # quote
                      log_line_prefix: "'%t '"


    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _g, _s, _p = __grains__, __salt__, __pillar__
        pkgs = __salt__['mc_pkgs.settings']()
        dist = pkgs['lts_dist']
        defaultPgVersion = '10'
        # default activated postgresql versions & settings:
        defaultVersions = []
        found_ports = []
        pg_conf = {
            'default': {
                'catalog': 'pg_catalog.french',
                'locale': 'fr_FR.UTF-8',
                'port': 5432,
                'unix_socket_directories': (
                    "'/var/run/postgresql'"),
                'ssl': 'true',
                'listen': ['*'],
                'datestyle': 'iso, dmy',
                'timezone': 'localtime',
                'max_connections': '100',
                'max_locks_per_transaction': '164',
                'max_pred_locks_per_transaction': '164',
                'log_line_prefix': '%t ',
                'log_timezone': 'localtime',
                'shared_buffers': '128MB',
                'ssl_cert_file': (
                    '/etc/ssl/certs/'
                    'ssl-cert-snakeoil.pem'),
                'ssl_key_file': (
                    '/etc/ssl/private/'
                    'ssl-cert-snakeoil.key'),
                'extras': {
                },
            },
        }
        for i in ['10', '9.6', '9.5', '9.4', '9.3', '9.2', '9.1']:
            # if we have old wrappers, include the old versions
            # to list of installed pgsql
            pgconf = '/etc/postgresql/{0}/main/postgresql.conf'.format(i)
            if os.path.exists(pgconf):
                with open(pgconf) as f:
                    content = f.read()
                    portm = PORT_RE.search(content)
                    if portm:
                        port = portm.groups()[0]
                        try:
                            port = int(port)
                            if port not in found_ports:
                                if port == 5432:
                                    defaultPgVersion = i
                                found_ports.append(port)
                                defaultVersions.append(i)
                                pg_vconf = pg_conf.setdefault(i, {})
                                pg_vconf.update({
                                    'port': port,
                                })
                        except (ValueError, TypeError) as exc:
                            pass
        if not defaultVersions:
            defaultVersions.append(defaultPgVersion)

        pgSettings = _s['mc_utils.defaults'](
            PREFIX, {
                'pgDbs': {},
                'postgresqlUsers': {},
                'dist': dist,
                'user': 'postgres',
                'version': defaultPgVersion,
                'versions': defaultVersions,
                'defaultPgVersion': defaultPgVersion,
                'encoding': 'utf8',
                'locale': 'fr_FR.UTF-8',
                'postgis_db': 'postgis',
                'pg_conf': pg_conf,
                'pg_hba':  [
                    {'comment': "# administration "},
                    {'type': 'local',
                     'db': 'all',
                     'user': 'postgres',
                     'address': '',
                     'method': 'peer'},
                    {'comment': "# local is for Unix socket connections only"},
                    {'type': 'local',
                     'db': 'all',
                     'user': 'all',
                     'address': '',
                     'method': 'peer'},
                    {'comment': "# IPv4 local connections:"},
                    {'type': 'host',
                     'db': 'all',
                     'user': 'all',
                     'address': '127.0.0.1/32',
                     'method': 'md5'},
                    {"comment": '# IPv6 local connections:'},
                    {'type': 'host',
                     'db': 'all',
                     'user': 'all',
                     'address': '::1/128',
                     'method': 'md5'},
                    {"comment": '# makina-states lxc inter communication'},
                    {'type': 'host',
                     'db': 'all',
                     'user': 'all',
                     'address': '10.5.0.0/16',
                     'method': 'md5'},
                    {'type': 'host',
                     'db': 'all',
                     'user': 'all',
                     'address': '0.0.0.0/0',
                     'method': 'md5'},
                ]
            }
        )

        postgis_pkgs = []
        client_pkgs = ['libpq-dev']
        packages = ['libpq-dev', 'postgresql-contrib-{version}']
        postgis = {}

        if __grains__.get('os', '') == 'Ubuntu':
            if LooseVersion(__grains__.get('osrelease', '0')) < LooseVersion('16.04'):
                for p in ['liblwgeom-dev']:
                    if p not in postgis_pkgs:
                        postgis_pkgs.append(p)

        for version in pgSettings['versions']:
            if LooseVersion(version) >= LooseVersion('10'):
                pgis_version = '2.4'
            elif LooseVersion(version) >= LooseVersion('9.6'):
                pgis_version = '2.3'
            elif LooseVersion(version) >= LooseVersion('9.4'):
                pgis_version = '2.2'
            else:
                pgis_version = '2.1'
            pgis_versions = postgis.setdefault(pgis_version, [])
            if not version in pgis_versions:
                pgis_versions.append(version)
            pgis = 'postgresql-{0}-postgis-{1}'.format(version, pgis_version)
            if pgis not in postgis_pkgs:
                postgis_pkgs.insert(0, pgis)
            scripts =  'postgresql-{0}-postgis-scripts'.format(version)
            if scripts not in postgis_pkgs:
                postgis_pkgs.append(scripts)
            if _g['os_family'] in ['Debian']:
                for pkgs, candidates in [
                    [client_pkgs, ['postgresql-client-{0}'.format(version)]],
                    [packages, ['postgresql-{0}',
                                'postgresql-server-dev-{0}',
                                'postgresql-{0}-pgextwlist']]
                ]:
                    for p in candidates:
                        p = p.format(version)
                        if p not in pkgs:
                            pkgs.append(p)

        data_second_round = {'packages': packages,
                             'postgis': postgis,
                             'client_pkgs': client_pkgs,
                             'postgis_pkgs': postgis_pkgs}
        second_round = _s['mc_utils.defaults'](PREFIX, copy.deepcopy(data_second_round))
        for i in data_second_round:
            pgSettings[i] = second_round[i]

        dpgconf = pgSettings['pg_conf']['default']
        dport = dpgconf['port']
        for i, ver in enumerate(pgSettings['versions']):
            pgconf = pgSettings['pg_conf'].setdefault(
                ver, OrderedDict())
            pgconf.setdefault('port', dport + i)
            pgSettings['pg_conf'][ver] = _s[
                'mc_utils.dictupdate'](
                    copy.deepcopy(dpgconf), pgconf)
        return pgSettings
    return _settings()


# vim:set et sts=4 ts=4 tw=0:
