#!/usr/bin/env python

'''
mc_pgsql / Postgresql related functions
=======================================
'''
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import re
import os
from salt.utils import context
from copy import deepcopy

import mc_states.utils


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
                    pg_version))['stdout']
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
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        localsettings = __salt__['mc_localsettings.settings']()
        nodetypes_registry = __salt__['mc_nodetypes.registry']()
        locations = localsettings['locations']
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

        #
        # default activated postgresql versions & settings:
        #
        defaultPgVersion = '9.3'
        pgSettings = __salt__['mc_utils.defaults'](
            'makina-states.services.postgresql', {
                'user': 'postgres',
                'version': defaultPgVersion,
                'defaultPgVersion': defaultPgVersion,
                'versions': [defaultPgVersion],
                'postgis': {'2.1': [defaultPgVersion, '9.2']},
                'postgis_db': 'postgis',
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
                    {'type': 'local',
                     'db': 'all',
                     'user': 'all',
                     'address': '127.0.0.1/32',
                     'method': 'md5'},
                    {"comment": '# IPv6 local connections:'},
                    {'type': 'local',
                     'db': 'all',
                     'user': 'all',
                     'address': '::1/128',
                     'method': 'md5'},
                ]
            }
        )
        pgSettings['pgDbs'] = pgDbs
        pgSettings['postgresqlUsers'] = postgresqlUsers
        return pgSettings
    return _settings()


# vim:set et sts=4 ts=4 tw=0:
