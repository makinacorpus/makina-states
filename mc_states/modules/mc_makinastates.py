#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import mc_states.api
import random
import json
import os
import logging
import re
import requests
from requests.auth import HTTPBasicAuth
from pprint import pprint


log = logging.getLogger(__name__)
J = os.path.join
DEFAULT_OS = 'ubuntu'
DEFAULT_RELEASE = 'vivid'
DEFAULT_IMG = None


def _ms():
    return __opts__['file_roots']['base'][0] + '/makina-states'


def virtualenv_release(ms_os=DEFAULT_OS,
                       release=DEFAULT_RELEASE,
                       upload=True,
                       img=DEFAULT_RELEASE):
    if not img:
        img = 'makinacorpus/makina-states-{0}-{1}-stable'.format(
            ms_os, release)
    ms_root = _ms()
    dest = 'virtualenv-{img}.tar.xz'.format(img=img.split('/')[1])
    dname = '{0}-venv-extracter'.format(img)
    infos = __salt__['docker.inspect_container'](dname)
    if infos['status']:
        __salt__['docker.remove_container'](dname, force=True)
    ret = __salt__['cmd.run_all'](
        'docker run --rm --name="${dname}" -v "{ms_root}":/makina-states \\'
        '-e XZ_OPTS="-9e" {img}\\'
        'tar cJf "/makina-states/docker/${dest}" /salt-venv'
        ''.format(img=img, dname=dname, dest=dest, ms_root=ms_root))
    if ret['retcode'] != 0:
        raise Exception('Extraction failed')
    if not upload:
        return
    u = "https://api.github.com/repos/makinacorpus/makina-states"
    tok = HTTPBasicAuth(data['gh_user'], data['gh_pw'])
    releases = requests.get("{0}/releases".format(u), auth=tok)
    pub = releases.json()
    fdv = 'attachedfiles'
    if fdv not in [a['name'] for a in pub]:
        cret = requests.post(
            "{0}/releases".format(u),
            auth=tok,
            data=json.dumps({'tag_name': fdv,
                             'name': fdv,
                             'body': fdv}))
        if 'created_at' not in cret.json():
            pprint(cret)
            raise ValueError('error creating release')
        pub = requests.get("{0}/releases".format(u), auth=tok).json()
        if fdv not in [a['name'] for a in pub]:
            raise ValueError('error getting release')
    release = [a for a in pub if a['name'] == fdv][0]
    assets = requests.get("{0}/releases/{1}/assets".format(
        u, release['id']), auth=tok).json()
    toup = dest
    if toup not in [a['name'] for a in assets]:
        fpath = J(ms_root, "docker/"+toup)
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
                   do_docker=True,
                   do_docker_upload=True,
                   do_venv_upload=True,
                   virtualenv=True):
    ms_root = _ms()
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
    if do_docker:
        log.info('Starting release building {0}/{1}'.format(ms_os, release))
        ret = __salt__['cmd.run_all'](
            'docker/build-scratch.sh', cwd=ms_root, use_vt=True, env=env)
    if virtualenv:
        virtualenv_release(
            ms_os=ms_os, release=release, img=img, upload=do_venv_upload)
# vim:set et sts=4 ts=4 tw=80:
