#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
'''
.. _module_mc_djutils:

mc_djutils / django helpers
============================================

'''

from datetime import datetime
import os
import copy
from pprint import pprint


CREATE_USER = """\
echo "SELECT 1 FROM pg_roles WHERE rolname='{db_user}';" |\\
    su postgres -c "psql -v ON_ERROR_STOP=1" | grep -q 1
if [ "x$?" = "x0" ]
then
    echo "User already exists, reset password"
    echo "ALTER USER {db_user} WITH ENCRYPTED PASSWORD '{db_pass}';" |\\
        su postgres -c "psql -v ON_ERROR_STOP=1"
    if [ "x$?" != "x0" ];then exit 1;fi
else
    echo "CREATE USER {db_user} ENCRYPTED PASSWORD '{db_pass}' CREATEDB;" |\\
        su postgres -c "psql -v ON_ERROR_STOP=1"
    if [ "x$?" != "x0" ];then exit 1;fi
fi
"""

CREATE_DB = """\
echo "SELECT 1 FROM pg_database WHERE datname='{db_name}';" | \\
    su postgres -c "psql -v ON_ERROR_STOP=1" | grep -q 1
if [ "x$?" = "x0" ]
then
    echo "Database already exists"
else
    su postgres -c "createdb -O {db_user} {db_name}"
    if [ "x$?" != "x0" ];then exit 1;fi
fi
"""

BACKUP = """#!/bin/bash
echo "SELECT 1 FROM pg_database WHERE datname='{db_name}';" | \\
    su postgres -c "psql -v ON_ERROR_STOP=1" | grep -q 1
if [ "x$?" = "x0" ]
then
    su postgres -c "pg_dump --no-privileges {db_name} -f {dump_filename}"
fi
"""


RESTORE = """#!/usr/bin/env bash
su postgres -c '\
        export PGPASSWORD="{db_pass}";\
        export PGUSER="{db_user}";\
        psql --host=127.0.0.1 -f {dump} {db_name}'
"""

DROP_DB = '''
echo "SELECT 1 FROM pg_database WHERE datname='{db_name}';" | \\
    su postgres -c "psql -v ON_ERROR_STOP=1" | grep -q 1
if [ "x$?" = "x0" ]
then
    su postgres -c "dropdb {db_name}"
fi
if [ "x$?" != "x0" ];then exit 1;fi
'''

HAS_PG_RUNNING = '''
set -e
ps afux|grep "postgres -D"|grep -v grep|grep -q postgres
'''


def run(host, script, *args, **kwargs):
    if host in ['localhost', '127.0.0.1']:
        kw = copy.deepcopy(kwargs)
        kw['python_shell'] = True
        return __salt__['cmd.run_all'](script, *args, **kw)
    else:
        return __salt__['mc_remote.ssh'](host, script, *args, **kwargs)


def test_pg(db_host=None, cfg='project'):
    if not db_host:
        data = __salt__['mc_project.get_configuration'](cfg)
        db = data['data']['django_settings']['DATABASES']['default']
        db_host = db['HOST']
    ret = run(db_host, HAS_PG_RUNNING)
    if ret['retcode']:
        pprint(ret)
        raise Exception('pg is not present')


def setup_database(db_host=None,
                   db_user=None,
                   db_pass=None,
                   db_name=None,
                   drop=False,
                   cfg='project'):
    '''
    Connect to a host with ssh

        create a pg user
        <maybe drop the db>
        create a db owned by the user
    '''
    data = __salt__['mc_project.get_configuration'](cfg)
    db = data['data']['django_settings']['DATABASES']['default']
    if not db_host:
        db_host = db['HOST']
    if not db_user:
        db_user = db['USER']
    if not db_pass:
        db_pass = db['PASSWORD']
    if not db_name:
        db_name = db['NAME']
    script = CREATE_USER
    if drop:
        script += DROP_DB
    script += CREATE_DB
    script = script.format(**locals())
    ret = run(host=db_host, script=script)
    if ret['retcode']:
        pprint(ret)
        raise Exception('setup failed')


def backup_database(db_host=None, db_name=None, cfg='project'):
    """ backup database before some critical operations """
    data = __salt__['mc_project.get_configuration'](cfg)
    db = data['data']['django_settings']['DATABASES']['default']
    if not db_host:
        db_host = db['HOST']
    if not db_name:
        db_name = db['NAME']
    dump_filename = '/tmp/{0}-{1}.dump'.format(
        db_name,
        datetime.now().strftime('%Y-%m-%d-%H-%M'))
    script = BACKUP.format(**locals())
    script += "exit $?\n"
    ret = run(host=db_host, script=script)
    if ret['retcode']:
        pprint(ret)
        raise Exception('dump failed')
    return dump_filename


def restore_from(db_host=None,
                 db_user=None,
                 db_pass=None,
                 db_name=None,
                 media=None,
                 dump=None,
                 orig_db_host=None,
                 orig_db_name=None,
                 orig_media=None,
                 orig_media_host=None,
                 skip_setup=False,
                 skip_db=False,
                 skip_media=False,
                 dev=None,
                 drop=True,
                 post_hook=None,
                 cfg='project'):
    '''
    Restore local django from a distant one
    Connect to host, get the pg backup
    connect to another host, load the pg backup
    sync medias
    run a post hook if any


    cfg
        name of the makina-states project to get configuration from
    '''
    data = __salt__['mc_project.get_configuration'](cfg)
    if dev is None:
        if data['default_env'] in ['dev', 'staging']:
            dev = True
    if post_hook and post_hook not in __salt__:
        raise Exception('post hook {0} does not exist'.format(post_hook))
    if not orig_media:
        orig_media = data['data'].get('orig_media')
    if not media:
        media = data['data'].get('media')
    if not orig_db_name:
        orig_db_name = data['data']['orig_db_name']
    if not orig_media_host:
        orig_media_host = data['data']['orig_media_host']
    if not orig_db_host:
        orig_db_host = data['data']['orig_db_host']
    db = data['data']['django_settings']['DATABASES']['default']
    if not db_host:
        db_host = db['HOST']
    if not db_user:
        db_user = db['USER']
    if not db_pass:
        db_pass = db['PASSWORD']
    if not db_name:
        db_name = db['NAME']
    if not skip_db:
        dodump = backup_database(db_host=db_host, db_name=db_name, cfg=cfg)
        if not dump:
            try:
                dump = backup_database(db_host=orig_db_host,
                                       db_name=orig_db_name, cfg=cfg)
                script = ('rsync -azv'
                          ' {orig_db_host}:{dump} {dump}').format(**locals())
                ret = __salt__['cmd.run_all'](script)
                if ret['retcode']:
                    raise Exception('Failed to download dump')
            finally:
                ormret = run(
                    host=orig_db_host,
                    script="\nrm -f {dump}\n".format(**locals()))
        if not skip_setup:
            setup_database(db_host,
                           db_user=db_user,
                           db_pass=db_pass,
                           db_name=db_name,
                           drop=drop,
                           cfg=cfg)
        script = ('rsync -azv'
                  ' {dump} {db_host}:{dump}').format(**locals())
        ret = __salt__['cmd.run_all'](script)
        if ret['retcode']:
            raise Exception('Failed to upload dump')
        try:
            script = RESTORE.format(**locals())
            ret = run(
                host=db_host, script=script)
            if ret['retcode']:
                raise Exception('Failed to restore & load  dump')
        finally:
            rmret = run(
                host=db_host,
                script="\nrm -f {dump}\n".format(**locals()))
    if media and orig_media and not skip_media:
        script = ('rsync -azPv'
                  ' {orig_media_host}:{orig_media}/ {media}/'
                  '').format(**locals())
        ret = __salt__['cmd.run_all'](script, use_vt=True)
        if ret['retcode']:
            raise Exception('Failed to download dump')
    if post_hook:
        __salt__[post_hook](
            db_host=db_host,
            db_user=db_user,
            db_pass=db_pass,
            db_name=db_name,
            media=media,
            dump=dump,
            orig_db_host=orig_db_host,
            orig_db_name=orig_db_name,
            orig_media=orig_media,
            orig_media_host=orig_media_host,
            skip_setup=skip_setup,
            skip_db=skip_db,
            skip_media=skip_media,
            dev=dev,
            drop=drop,
            post_hook=post_hook,
            cfg=cfg,
            data=data)
# vim:set et sts=4 ts=4 tw=80:
