#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import re
import os
from salt.utils import context
from copy import deepcopy


PORT_RE = re.compile('port\s*=\s*([0-9]+)[^0-9]*$', re.M | re.U | re.S)
SOCKET_RE = re.compile(
    'unix_socket_director(y|ies)\s*=\s*["\']([^"\']+)["\'].*$',
    re.M | re.U | re.S)


def wrapper(wrappy):
    def wfunc(name, *args, **kw):
        globs = dict([(k, v) for k, v in globals().items()
                      if not k in ['wrapper', 'args', 'kw',
                                   'PORT_RE', 'SOCKET_RE', 'os', 're']])
        pg_version = kw.get('pg_version', None)
        if pg_version is not None:
            db_host = kw.get('db_host', None)
            db_port = kw.get('db_port', None)
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

# vim:set et sts=4 ts=4 tw=80:
