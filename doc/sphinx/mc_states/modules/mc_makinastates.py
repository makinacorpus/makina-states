#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_makinastates:

mc_makinastates
===============================================



'''

import mc_states.api
import random
import json
import os
import logging
import re
import requests
from requests.auth import HTTPBasicAuth
from pprint import pprint
from mc_states.version import VERSION


log = logging.getLogger(__name__)
__name = 'config'
J = os.path.join
DEFAULT_OS = 'ubuntu'
DEFAULT_RELEASE = 'xenial'
DEFAULT_IMG = None
PREFIX = 'makina-states.{0}'.format(__name)


def _ms():
    return __opts__['file_roots']['base'][0] + '/makina-states'


def version():
    '''return without much salt machinery the current version'''
    return VERSION


def settings():
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        data = __salt__['mc_utils.defaults'](
            PREFIX, {
                'github_user': None,
                'github_password': None,
                'releases': {
                    'ubuntu': ['trusty', 'vivid', 'xenial']
                }
            }
        )
        return data
    return _settings()

def _get_img(img, ms_os, release):
    if not img:
        img = 'makinacorpus/makina-states-{0}-{1}-v2'.format(
            ms_os.capitalize(), release)
    return img


def virtualenv_release(ms_os=DEFAULT_OS,
                       release=DEFAULT_RELEASE,
                       extract=True,
                       upload=True,
                       logfile=None,
                       img=None):

    ms_root = _ms()
    data = settings()
    img = _get_img(img, ms_os, release)
    bimg = img.split('/')[1]
    dest = 'docker/virtualenv-{img}.tar.xz'.format(img=bimg)
    dname = '{0}-venv-extracter'.format(bimg)
    if extract:
        infos = __salt__['docker.inspect_container'](dname)
        if infos['status']:
            __salt__['docker.remove_container'](dname, force=True)
        cmd = ('docker run --rm --name="{dname}" -v "{ms_root}":/makina-states'
               ' -e XZ_OPTS="-9e" {img}'
               ' tar cJf "/makina-states/{dest}" /srv/makina-states/venv'
               '').format(img=img, dname=dname, dest=dest, ms_root=ms_root)
        ret = __salt__['cmd.run_all'](cmd, cwd=ms_root, python_shell=True)
        if ret['retcode'] != 0:
            print(ret['stdout'])
            print(ret['stderr'])
            raise Exception('Extraction failed')
    if not upload:
        return
    orga = __salt__['mc_salt.get_ms_url']().replace(
        '.git', '').split('github.com/')[1]
    u = "https://api.github.com/repos/" + orga
    tok = HTTPBasicAuth(data['github_user'], data['github_password'])
    releases = requests.get("{0}/releases".format(u), auth=tok)
    pub = releases.json()
    fdv = 'attachedfiles'
    if fdv not in [a['tag_name'] for a in pub]:
        cret = requests.post(
            "{0}/releases".format(u),
            auth=tok,
            data=json.dumps({'tag_name': fdv,
                             'name': fdv,
                             'body': fdv}))
        if 'created_at' not in cret.json():
            pprint(cret)
            raise ValueError('error creating release')
        log.info('Created release {0}/{1}'.format(u, fdv))
        pub = requests.get("{0}/releases".format(u), auth=tok).json()
        if fdv not in [a['tag_name'] for a in pub]:
            raise ValueError('error getting release')
    release = [a for a in pub if a['tag_name'] == fdv][0]
    assets = requests.get("{0}/releases/{1}/assets".format(
        u, release['id']), auth=tok).json()
    toup = os.path.basename(dest)
    fpath = J(ms_root, dest)
    if not os.path.exists(fpath):
        raise Exception('Release file is not here: {0}'.format(fpath))
    if toup in [a['name'] for a in assets]:
        asset = [a for a in assets if a['name'] == toup][0]
        cret = requests.delete(asset['url'], auth=tok)
        if not cret.ok:
            raise ValueError('error deleting release')
    log.info('Upload of {0} started'.format(toup))
    size = os.stat(fpath).st_size
    with open(fpath) as fup:
        fcontent = fup.read()
        upurl = re.sub(
            '{.*', '', release['upload_url']
        )+'?name={0}&size={1}'.format(toup, size)
        cret = requests.post(
            upurl, auth=tok,
            data=fcontent,
            headers={
                'Content-Type':
                'application/x-xz'})
        jret = cret.json()
        if jret.get('size', '') != size:
            pprint(jret)
            raise ValueError('upload failed')


def docker_release(ms_os=DEFAULT_OS,
                   release=DEFAULT_RELEASE,
                   img=DEFAULT_IMG,
                   branch=None,
                   changeset=None,
                   env=None,
                   logfile=None,
                   do_docker=True,
                   do_docker_upload=True,
                   venv_extract=True,
                   venv_upload=True,
                   virtualenv=False):
    ms_root = _ms()
    img = _get_img(img, ms_os, release)
    if env is None:
        env = {}
    for i, v in {
        'MS_OS': ms_os,
        'MS_OS_RELEASE': release
    }.items():
        env.setdefault(i, v)
    if changeset:
        env['MS_CHANGESET'] = changeset
    if branch:
        env['MS_BRANCH'] = branch
    if not logfile:
        logfile = os.path.join(
            'docker/logfile-{0}{1}.log'.format(ms_os, release))
    if do_docker:
        log.info('Starting release building {0}/{1}'.format(ms_os, release))
        log.info('You can attach build log by tail -f {0}'.format(
            J(ms_root, logfile)))
        ret = __salt__['cmd.run_all'](
            'docker/build-scratch.sh>{0}'.format(logfile),
            python_shell=True, cwd=ms_root, env=env)
        if ret['retcode'] != 0:
            print(ret['stdout'])
            print(ret['stderr'])
            raise Exception('docker building failed')
    if virtualenv:
        virtualenv_release(
            ms_os=ms_os, release=release, img=img,
            extract=venv_extract, upload=venv_upload)
# vim:set et sts=4 ts=4 tw=80:
