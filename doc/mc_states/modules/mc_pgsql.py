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
        grains = __grains__
        pillar = __pillar__
        #
        # PostGRESQL:  (services.db.postgresql)
        # default postgresql/ grains configured databases (see service doc)
        #
        pgDbs = {}
        for dbk, data in pillar.items():
            if dbk.endswith('-makina-postgresql'):
                db = data.get('name', dbk.split('-makina-postgresql')[0])
                pgDbs.update({db: data})
        #
        # default postgresql/ grains configured users (see service doc)
        #
        postgresqlUsers = {}
        for userk, data in pillar.items():
            if userk.endswith('-makina-services-sql-user'):
                userk = data.get(
                    'name',
                    userk.replace('-makina-services-postgresql-user', ''))
                if data.get('groups', None):
                    if isinstance(data['groups'], basestring):
                        data['groups'] = data['groups'].split(',')
                postgresqlUsers.update({userk: data})
        pkgs = __salt__['mc_pkgs.settings']()
        dist = pkgs['lts_dist']
        if __grains__.get('os', '') == 'Ubuntu':
            if LooseVersion(__grains__.get('osrelease', '0')) >= LooseVersion('16.04'):
                xenial_onward = True
                defaultPgVersion = '9.5'
                pgis_version = '2.2'
            else:
                xenial_onward = False
                pgis_version = '2.1'
                defaultPgVersion = '9.5'

        #
        # default activated postgresql versions & settings:
        #
        for i in ['9.4', '9.3', '9.2', '9.1']:
            # if we have old wrappers, include the old versions
            # to list of installed pgsql
            if os.path.exists('/usr/bin/psql-{0}'.format(i)):
                defaultPgVersion = i
                break
        defaultVersions = [defaultPgVersion]
        pgSettings = __salt__['mc_utils.defaults'](
            'makina-states.services.db.postgresql', {
                'dist': dist,
                'xenial_onward': xenial_onward,
                'user': 'postgres',
                'version': defaultPgVersion,
                'defaultPgVersion': defaultPgVersion,
                'versions': defaultVersions,
                'encoding': 'utf8',
                'locale': 'fr_FR.UTF-8',
                'postgis': {
                    pgis_version: defaultVersions + ['9.2']
                },
                'postgis_db': 'postgis',
                'pg_conf': {
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
                        }
                    },
                },
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
        dpgconf = pgSettings['pg_conf']['default']
        dport = dpgconf['port']
        for i, ver in enumerate(pgSettings['versions']):
            pgconf = pgSettings['pg_conf'].setdefault(
                ver, OrderedDict())
            pgconf.setdefault('port', dport + i)
            pgSettings['pg_conf'][ver] = __salt__[
                'mc_utils.dictupdate'](
                    copy.deepcopy(dpgconf), pgconf)
            pgSettings['pg_conf'][ver][
                'unix_socket_directories']
        pgSettings['pgDbs'] = pgDbs
        pgSettings['postgresqlUsers'] = postgresqlUsers
        return pgSettings
    return _settings()


# vim:set et sts=4 ts=4 tw=0:
