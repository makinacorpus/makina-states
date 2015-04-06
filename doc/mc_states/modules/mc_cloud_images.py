#!/usr/bin/env python
'''
.. _module_mc_cloud_images:

mc_cloud_images / cloud images related functions
================================================



Please also have a look at the runner.
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import os
import copy
import yaml
import mc_states.api

from mc_states import saltapi

from mc_states.runners import mc_lxc
from mc_states.modules.mc_lxc import (
    is_lxc)

from salt.utils.odict import OrderedDict
__name = 'mc_cloud_images'

log = logging.getLogger(__name__)
_errmsg = saltapi._errmsg
PROJECT_PATH = 'project/makinacorpus/makina-states'
SFTP_URL = 'frs.sourceforge.net:/home/frs/{0}'.format(PROJECT_PATH)
TARGET = '/var/lib/lxc/makina-states'
PREFIX = 'makina-states.cloud.images'
IMG_URL = ('https://downloads.sourceforge.net/makinacorpus'
           '/makina-states/'
           '{1}-lxc-{0}.tar.xz')


def complete_images(data):
    root = data['root']
    images = data['lxc'].setdefault('images', OrderedDict())
    images.setdefault('makina-states-trusty', {})
    for img in [i for i in images]:
        defaults = OrderedDict()
        defaults['builder_ref'] = '{0}-lxc-ref.foo.net'.format(img)
        images[img] = __salt__['mc_utils.dictupdate'](
            defaults, images[img])
        md5_file = os.path.join(root,
                                ('makina-states/versions/'
                                 '{0}-lxc_version.txt.md5').format(img))
        ver_file = os.path.join(root,
                                ('makina-states/versions/'
                                 '{0}-lxc_version.txt').format(img))
        if (
            not os.path.exists(ver_file)
            and not os.path.exists(md5_file)
        ):
            continue
        with open(ver_file) as fic:
            images[img]['lxc_tarball_ver'] = fic.read().strip()
        with open(md5_file) as fic:
            images[img]['lxc_tarball_md5'] = fic.read().strip()
        images[img]['lxc_tarball'] = IMG_URL.format(
            images[img]['lxc_tarball_ver'], img)
        images[img]['lxc_tarball_name'] = os.path.basename(
            images[img]['lxc_tarball'])
    return data


def default_settings():
    '''
    cloudcontroller images templates settings

    /

        lxc
            specific lxc images settings

            images
                mapping of images informations
            cron_sync
                activate the img synchronnizer
            cron_hour
                hour for the img synchronnizer
            cron_minute
                minute for the img synchronnizer
    '''
    _s = __salt__
    data = {'root': '/srv/mastersalt/makina-states',
            'kvm': {'images': OrderedDict()},
            'lxc': {'images_root': '/var/lib/lxc',
                    'cron_sync': False,
                    'images': OrderedDict(),
                    'cron_hour': '3',
                    'cron_minute': '3'}}
    data = complete_images(data)
    return data


def extpillar_settings(id_=None, limited=False, ttl=30):
    def _do(id_=None, limited=False):
        cid = __opts__['id']
        _s = __salt__
        extdata = _s['mc_pillar.get_global_clouf_conf']('images')
        mextdata = _s['mc_pillar.get_global_clouf_conf'](
            'images_{0}'.format(cid))
        data = {}
        cloud_settings = _s['mc_cloud.extpillar_settings']()
        is_devhost = _s['mc_nodetypes.is_devhost']()
        cron_sync = True
        if (is_lxc() or is_devhost):
            cron_sync = False
        data = _s['mc_utils.dictupdate'](
            _s['mc_utils.dictupdate'](
                default_settings(), extdata),
            mextdata)
        if id_:
            cextdata = _s['mc_pillar.get_global_clouf_conf'](
                'images_{0}'.format(id_))
            data = _s['mc_utils.dictupdate'](data, cextdata)
        data['root'] = cloud_settings['root']
        data['lxc']['cron_sync'] = cron_sync
        data = complete_images(data)
        data = _s['mc_utils.format_resolve'](data)
        return data
    cache_key = 'mc_cloud_images.extpillar_settings{0}{1}'.format(
        id_, limited)
    return __salt__['mc_utils.memoize_cache'](_do, [id_, limited], {}, cache_key, ttl)


def ext_pillar(id_, prefixed=True, *args, **kw):
    '''
    Images extpillar
    '''
    _s = __salt__
    limited = kw.get('limited', False)
    expose = False
    if _s['mc_cloud.is_a_cloud_member'](id_):
        expose = True
    data = {}
    if expose:
        data = extpillar_settings(id_, limited=limited)
    if prefixed:
        data = {PREFIX: data}
    return data


'''
To execute on node after pillar is loaded
'''


def settings(ttl=60):
    '''
    Images registry
    '''
    def _do():
        _s = __salt__
        cloud_settings = _s['mc_cloud.settings']()
        root = cloud_settings['root']
        nt_registry = __salt__['mc_nodetypes.registry']()
        cron_sync = None
        if (
                nt_registry['is']['devhost']
                or nt_registry['is']['lxccontainer']
                or __salt__['mc_utils.get'](
                    'makina-states.cloud.is.vm', False)
        ):
            cron_sync = False
        data = __salt__['mc_utils.defaults'](PREFIX, default_settings())
        data['root'] = root
        data = complete_images(data)
        if cron_sync is not None:
            data['lxc']['cron_sync'] = cron_sync
        return data
    cache_key = '{0}.{1}'.format(__name, 'settings')
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def _run(cmd):
    return __salt__['cmd.run_all'](cmd, python_shell=True)


def sf_release(images=None):
    '''Upload the makina-states container lxc tarball to sourceforge;
    this is used in makina-states.cloud.lxc as a base
    for other containers.

    pillar/grain parameters:

        makina-states.sf user

    Do a release::

        salt-call -all mc_lxc.sf_release
    '''
    _s = __salt__
    _cli = _s.get
    imgSettings = _s['mc_cloud_images.settings']()
    if isinstance(images, basestring):
        images = [images]
    if images is None:
        images = [a for a in imgSettings['lxc']['images']]
    gret = {'rets': [], 'result': True, 'comment': 'sucess', 'changes': {}}
    mc_lxc.sync_image_reference_containers(imgSettings, gret,
                                           __salt__from_exec=_s,
                                           _cmd_runner=_run, force=True)
    if not gret['result']:
        return gret
    for img in images:
        imgdata = imgSettings['lxc']['images'][img]
        ret = {'result': True, 'comment': '', 'trace': ''}
        root = _cli('mc_utils.get')('file_roots')['base'][0]
        ver_file = os.path.join(
            root,
            'makina-states/versions/{0}-lxc_version.txt'.format(img))
        try:
            cur_ver = int(open(ver_file).read().strip())
        except:
            cur_ver = 0
        next_ver = cur_ver + 1
        user = _cli('mc_utils.get')('makina-states.sf_user', 'kiorky')
        dest = '{1}-lxc-{0}.tar.xz'.format(next_ver, img)
        container_p = '/var/lib/lxc/{0}'.format(img)
        fdest = '/var/lib/lxc/{0}'.format(dest)
        if not os.path.exists(container_p):
            _errmsg(ret, '{0} container does not exists'.format(img))
        aclf = os.path.join(container_p, 'acls.txt')
        if not os.path.exists(fdest):
            cmd = 'getfacl -R . > acls.txt'
            cret = _cli('cmd.run_all')(
                cmd, cwd=container_p, python_shell=True, salt_timeout=60 * 60)
            if cret['retcode']:
                _errmsg('error with acl')
            # ignore some paths in the acl file
            # (we have no more special cases, but leave this code in case)
            ignored = []
            acls = []
            with open(aclf) as f:
                skip = False
                for i in f.readlines():
                    for path in ignored:
                        if path in i:
                            skip = True
                    if not i.strip():
                        skip = False
                    if not skip:
                        acls.append(i)
            with open(aclf, 'w') as w:
                w.write(''.join(acls))
            cmd = ('tar cJfp {0} . '
                   '--ignore-failed-read --numeric-owner').format(fdest)
            cret = _cli('cmd.run_all')(
                cmd,
                cwd=container_p,
                python_shell=True,
                env={'XZ_OPT': '-7e'},
                salt_timeout=60 * 60)
            if cret['retcode']:
                _errmsg(ret, 'error with compressing')
        cmd = 'rsync -avzP {0} {1}@{2}/{3}.tmp'.format(
            fdest, user, SFTP_URL, dest)
        cret = _cli('cmd.run_all')(
            cmd, cwd=container_p, python_shell=True, salt_timeout=8 * 60 * 60)
        if cret['retcode']:
            return _errmsg(ret, 'error with uploading')
        cmd = 'echo "rename {0}.tmp {0}" | sftp {1}@{2}'.format(dest,
                                                                user,
                                                                SFTP_URL)
        cret = _cli('cmd.run_all')(
            cmd, cwd=container_p, python_shell=True, salt_timeout=60)
        if cret['retcode']:
            _errmsg(ret, 'error with renaming')
        cmd = "md5sum {0} |awk '{{print $1}}'".format(fdest)
        cret = _cli('cmd.run_all')(
            cmd, cwd=container_p, python_shell=True, salt_timeout=60 * 60)
        if cret['retcode']:
            _errmsg(ret, 'error with md5')
        with open(ver_file + ".md5", 'w') as f:
            f.write("{0}".format(cret['stdout']))
        with open(ver_file, 'w') as f:
            f.write("{0}".format(next_ver))
        cmd = (
            ('git add *-lxc*version*txt*;'
             'git commit versions -m "new lxc release {0}";'
             'git push').format(next_ver))
        cret = _cli('cmd.run_all')(cmd,
                                   cwd=root + '/makina-states',
                                   python_shell=True,
                                   salt_timeout=60)
        if cret['retcode']:
            _errmsg(ret, 'error with commiting new version')
        ret['comment'] = 'release {0} done'.format(next_ver)
        if not ret['result']:
            gret['result'] = False
            gret['comment'] = 'failure'
        gret['rets'].append(ret)
    return gret


# vim:set et sts=4 ts=4 tw=80:
