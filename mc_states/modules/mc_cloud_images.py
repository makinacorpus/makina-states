#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function
# pylint: disable=W0105
'''
.. _module_mc_cloud_images:

mc_cloud_images / cloud images release managment & delivery
===========================================================



Please also have a look at the runner.
'''

# Import python libs
import traceback
import logging
import os
import re
import copy
import shutil
import salt.exceptions
from mc_states import saltapi

from distutils.version import LooseVersion
from mc_states.runners import mc_lxc
from mc_states.modules.mc_lxc import (
    is_lxc)
from salt.utils.odict import OrderedDict
from mc_states.modules.mc_pillar import PILLAR_TTL
__name = 'mc_cloud_images'

six = saltapi.six
log = logging.getLogger(__name__)
_errmsg = saltapi._errmsg
PROJECT_PATH = 'project/makinacorpus/makina-states'
SFTP_URL = 'frs.sourceforge.net:/home/frs/{0}'.format(PROJECT_PATH)
TARGET = '/var/lib/lxc/makina-states'
PREFIX = 'makina-states.cloud.images'
IMG_URL = ('https://downloads.sourceforge.net/makinacorpus'
           '/makina-states/'
           '{img}-{flavor}-{ver}.tar.xz')
LXC_IMAGES = OrderedDict([('makina-states-vivid', {}),
                          ('makina-states-trusty', {}),
                          ('makina-states-precise', {})])
DEFAULT_OS = 'ubuntu'
RELEASES = {
    'ubuntu': {
        'default': 'vivid',
        'releases': ['wily', 'utopic', 'vivid', 'trusty', 'precise']
    }

}
# THIS IS A NON FINISHEP WIP TO REFACTOR IMAGE SETTINGS
IMAGES = OrderedDict([
    ('lxc', OrderedDict([
        ('ubuntu-vivid', {
            'create': '-t ubuntu -- -r vivid --mirror {mirror}'
        }),
        ('makina-states-vivid', {
            'clone': 'ubuntu-vivid',
            'bootsalt': True}),
    ])),
    ('docker', OrderedDict([
        ('makina-states/ubuntu-vivid-raw', {
            'from_lxc': 'makina-states-vivid'}),
        ('ubuntu-vivid-systemd-debug', {
            'from': 'makina-states:ubuntu-vivid'})
    ]))
])


# shortcuts
ImgError = saltapi.ImgError
ImgStepError = saltapi.ImgStepError


def _imgerror(msg, cret=None):
    msg = saltapi.rich_error(ImgError, msg, cret)
    return msg


def complete_images(data):
    root = data['root']
    if 'makina-states' not in root:
        nroot = os.path.join(root, 'makina-states')
        if os.path.exists(nroot):
            root = nroot
    images = data['lxc'].setdefault('images', OrderedDict())
    images = __salt__['mc_utils.dictupdate'](
        images, copy.deepcopy(LXC_IMAGES))
    for img in [i for i in images]:
        defaults = OrderedDict()
        defaults['builder_ref'] = '{0}-lxc-ref.foo.net'.format(img)
        images[img] = __salt__['mc_utils.dictupdate'](defaults, images[img])
        images[img].setdefault('flavors', ['lxc', 'standalone'])
        for flavor in images[img]['flavors']:
            md5_file = os.path.join(root,
                                    ('versions/'
                                     '{0}-{1}_version.txt.md5'
                                     '').format(img, flavor))
            ver_file = os.path.join(root,
                                    ('versions/'
                                     '{0}-{1}_version.txt'
                                     '').format(img, flavor))
            if (
                not os.path.exists(ver_file) and
                not os.path.exists(md5_file)
            ):
                log.info('lxc/{0} is not released yet, disabling'.format(img))
                continue
            with open(ver_file) as fic:
                ver = images[img][
                    '{0}_tarball_ver'.format(flavor)] = fic.read().strip()
            with open(md5_file) as fic:
                images[img][
                    '{0}_tarball_md5'.format(flavor)] = fic.read().strip()
            img_url = images[img].get('{0}_url'.format(
                flavor), IMG_URL).format(
                    img=img, flavor=flavor, ver=ver)
            img_url = images[img].setdefault('{0}_url'.format(flavor),
                                             img_url)
            tarball = images[img].setdefault('{0}_tarball'.format(flavor),
                                             img_url)
            images[img].setdefault('{0}_tarball_name'.format(flavor),
                                   os.path.basename(tarball))
    return data


def default_settings():
    '''
    cloudcontroller images templates settings

    /

        sftp_user
            user to use to publish imgs via sftp
        git_url
            makina-states fork (git url (ssh based))
            to publish new images to
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
            'git_url': 'ssh://github.com/makinacorpus/makina-states',
            'sftp_url': SFTP_URL,
            'sftp_user': _s['mc_utils.get']('makina-states.sf_user',
                                            'kiorky'),
            'lxc': {'images_root': '/var/lib/lxc',
                    'cron_sync': False,
                    'default': [a for a in LXC_IMAGES][0],
                    'images': OrderedDict(),
                    'cron_hour': '3',
                    'cron_minute': '3'}}
    data = complete_images(data)
    return data


def extpillar_settings(id_=None, limited=False, ttl=PILLAR_TTL):
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
        if is_lxc() or is_devhost:
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
    return __salt__['mc_utils.memoize_cache'](
        _do, [id_, limited], {}, cache_key, ttl)


def ext_pillar(id_, prefixed=True, ttl=PILLAR_TTL, *args, **kw):
    '''
    Images extpillar
    '''
    def _do(id_, prefixed, args, kw):
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
    cache_key = '{0}.{1}.{2}{3}'.format(
        __name, 'ext_pillar', id_, prefixed)
    return __salt__['mc_utils.memoize_cache'](
        _do, [id_, prefixed, args, kw], {}, cache_key, ttl)


# pylint: disable=W0105
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
            nt_registry['is']['devhost'] or
            nt_registry['is']['lxccontainer'] or
            __salt__['mc_utils.get'](
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


def get_vars(**kwargs):
    _s = __salt__
    csettings = settings()
    data = {'file_root': _s['mc_utils.get']('file_roots')['base'][0],
            'tarball': '{container}-{flavor}-{next_ver}.tar.xz',
            'absolute_tarball': '{root}/{tarball}',
            'root': '/var/lib/lxc',
            'container_path': '{root}/{container}',
            'rootfs': '{container_path}/rootfs',
            'ver_file':
            '{file_root}/makina-states/versions'
            '/{container}-{flavor}_version.txt',
            'user': csettings['sftp_user'],
            'sftp_url': csettings['sftp_url'],
            'git_url': csettings['git_url']}
    if kwargs:
        data.update(copy.deepcopy(kwargs))
    data.setdefault('flavor', 'standalone')
    data.setdefault('container', 'makina-states-vivid')
    data['container'] = data['container'].replace('imgbuild-', '')
    data = _s['mc_utils.format_resolve'](data)
    try:
        cur_ver = int(open(data['ver_file']).read().strip())
    except (IOError, OSError,
            ValueError, TypeError, KeyError,
            UnicodeEncodeError, UnicodeDecodeError):
        cur_ver = 0
    next_ver = cur_ver + 1
    data['cur_ver'] = cur_ver
    data['next_ver'] = next_ver
    data = _s['mc_utils.format_resolve'](data)
    return data


def snapshot(container, flavor, *args, **kwargs):
    kwargs['container'] = container
    kwargs['flavor'] = flavor
    gvars = get_vars(**kwargs)
    cret = mc_lxc.snapshot_container(_run, gvars['rootfs'])
    if cret['retcode']:
        raise _imgerror(
            '{0}/{1}: snapshot failed'.format(container, flavor),
            cret=cret)
    return cret


def snapshot_standalone(container, *args, **kwargs):
    return snapshot(container, 'standalone', *args, **kwargs)


def snapshot_lxc(container, *args, **kwargs):
    return snapshot(container, 'lxc', *args, **kwargs)


def save_acls(container, flavor, *args, **kwargs):
    _s = __salt__
    kwargs['container'] = container
    kwargs['flavor'] = flavor
    gvars = get_vars(**kwargs)
    aclf = os.path.join(gvars['container_path'], 'acls.txt')
    # all release flavors are releated, so we just check one here
    # and this must be the last one produced
    # if the last one is not present, all flavors will be rebuilt
    log.info('{container}/{flavor}: archiving acls files'.format(**gvars))
    aclsf = []
    for root in [gvars['rootfs'], gvars['container_path']]:
        cmd = 'getfacl -R . > acls.txt'
        cret = _s['cmd.run_all'](
            cmd, cwd=root, python_shell=True, salt_timeout=60*60)
        if cret['retcode']:
            raise _imgerror(
                '{container}/{flavor}: error with acl'.format(**gvars),
                cret=cret)
        aclsf.append(os.path.join(root, 'acls.txt'))
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
    return aclsf


def save_acls_lxc(container, *args, **kwargs):
    return save_acls(container, 'lxc', *args, **kwargs)


def save_acls_standalone(container, *args, **kwargs):
    return save_acls(container, 'standalone', *args, **kwargs)


def get_ret(**kwargs):
    ret = kwargs.get('ret',
                     {'result': True,
                      'comment': '',
                      'changes': {}})
    return ret


def archive_standalone(container, *args, **kwargs):
    _s = __salt__
    kwargs['container'] = container
    kwargs.setdefault('flavor', 'standalone')
    gvars = get_vars(**kwargs)
    if os.path.exists(gvars['absolute_tarball']):
        log.info('{container}/{flavor}: {absolute_tarball} exists'
                 ', delete it to redo'.format(**gvars))
    else:
        try:
            cmd = ('tar cJfp {absolute_tarball} '
                   ' etc/cron.d/*salt*'
                   ' etc/logrotate.d/*salt*'
                   ' etc/init.d/mastersalt-*'
                   ' etc/init.d/salt-*'
                   ' etc/init/mastersalt-*'
                   ' etc/systemd/system/mastersalt-*'
                   ' etc/systemd/system/salt-*'
                   ' etc/init/salt-*'
                   ' etc/{{mastersalt,salt}}'
                   ' srv/{{mastersalt-pillar,pillar}}'
                   ' srv/{{salt,mastersalt}}'
                   ' usr/bin/mastersalt-*'
                   ' usr/bin/mastersalt'
                   ' usr/bin/salt-*'
                   ' salt-venv'
                   ' usr/bin/salt'
                   ' var/cache/{{mastersalt,salt}}'
                   ' var/run/{{mastersalt,salt}}'
                   ' --ignore-failed-read --numeric-owner').format(**gvars)
            log.info('{container}/{flavor}: '
                     'archiving in {absolute_tarball}'.format(**gvars))
            cret = _s['cmd.run_all'](
                cmd,
                cwd=gvars['rootfs'],
                python_shell=True,
                env={'XZ_OPT': '-7e'},
                salt_timeout=60*60)
            if cret['retcode']:
                raise _imgerror(
                    '{container}/{flavor}: '
                    'error with compressing {absolute_tarball}'.format(**gvars),
                    cret=cret)
        except (Exception,) as exc:
            if os.path.exists(gvars['absolute_tarball']):
                os.remove(gvars['absolute_tarball'])
                raise exc
    return gvars['absolute_tarball']


def archive_lxc(container, *args, **kwargs):
    _s = __salt__
    kwargs['container'] = container
    kwargs['flavor'] = 'lxc'
    gvars = get_vars(**kwargs)
    if os.path.exists(gvars['absolute_tarball']):
        log.info('{container}/{flavor}: {absolute_tarball} exists,'
                 ' delete it to redo'.format(**gvars))
    else:
        cmd = ('tar cJfp {absolute_tarball} . '
               '--ignore-failed-read --numeric-owner').format(**gvars)
        try:
            log.info('{container}/{flavor}: '
                     'archiving in {absolute_tarball}'.format(**gvars))
            cret = _s['cmd.run_all'](
                cmd,
                cwd=gvars['container_path'],
                python_shell=True,
                env={'XZ_OPT': '-7e'},
                salt_timeout=60*60)
            if cret['retcode']:
                raise _imgerror(
                    '{container}/{flavor}: '
                    'error with compressing {absolute_tarball}'.format(**gvars),
                    cret=cret)
        except (Exception, KeyboardInterrupt) as exc:
            if os.path.exists(gvars['absolute_tarball']):
                os.remove(gvars['absolute_tarball'])
                raise exc
    return gvars['absolute_tarball']


def upload(container, flavor, *args, **kwargs):
    kwargs['container'] = container
    kwargs.setdefault('flavor', flavor)
    gvars = get_vars(**kwargs)
    _s = __salt__
    if not os.path.exists(gvars['absolute_tarball']):
        raise _imgerror(
            '{container}/{flavor}: '
            'release is not done'.format(**gvars))
    failed, cret = False, None
    cmd = ('rsync -avzP {absolute_tarball}'
           ' {user}@{sftp_url}/{tarball}.tmp').format(**gvars)
    cret = _s['cmd.run_all'](
        cmd, python_shell=True, use_vt=True, salt_timeout=8*60*60)
    if cret['retcode']:
        failed = True
    cmd = ('echo "rename {tarball}.tmp {tarball}" '
           '| sftp {user}@{sftp_url}').format(**gvars)
    cret = _s['cmd.run_all'](
        cmd, python_shell=True, use_vt=True, salt_timeout=60)
    if cret['retcode']:
        failed = True
    if failed:
        # bindly try to remove the files
        for i in ['', '.tmp']:
            gvars['sufsuf'] = i
            cmd = ('echo "rm {tarball}{sufsuf}" '
                   '| sftp {user}@{sftp_url}').format(**gvars)
            cret = _s['cmd.run_all'](
                cmd, python_shell=True, use_vt=True, salt_timeout=60)
        raise _imgerror(
            '{container}/{flavor}: '
            'error with remote renaming'.format(**gvars),
            cret=cret)
    return '{sftp_url}/{tarball}'.format(**gvars)


def upload_standalone(container, *args, **kwargs):
    return upload(container, 'standalone')


def upload_lxc(container, *args, **kwargs):
    return upload(container, 'lxc')


def publish_release(container, flavor, *args, **kwargs):
    _s = __salt__
    gvars = get_vars(container=container, flavor=flavor)
    cmd = "md5sum {absolute_tarball} |awk '{{print $1}}'".format(**gvars)
    cret = _s['cmd.run_all'](
        cmd, cwd=gvars['root'], python_shell=True, salt_timeout=60*60)
    if cret['retcode']:
        raise _imgerror('{container}/{flavor}:'
                        ' error with md5'.format(**gvars),
                        cret=cret)
    with open(gvars['ver_file'] + ".md5", 'w') as f:
        f.write("{0}".format(cret['stdout']))
    with open(gvars['ver_file'], 'w') as f:
        f.write("{next_ver}".format(**gvars))
    cmd = ('git add versions/*-{flavor}_*;'
           'git add versions/*-{flavor}_*;'
           'git commit'
           ' -m "new release {container}/{flavor}/{next_ver}"'
           '  versions/*-{flavor}_*;'
           'git push {git_url}').format(**gvars)
    cret = _s['cmd.run_all'](
        cmd,
        cwd=gvars['file_root'] + '/makina-states',
        python_shell=True,
        salt_timeout=60)
    if cret['retcode']:
        _imgerror('{container}/{flavor}: '
                  'error with commiting new version'.format(**gvars),
                  cret=cret)


def publish_release_lxc(container, *args, **kwargs):
    return publish_release(container, 'lxc', *args, **kwargs)


def publish_release_standalone(container, *args, **kwargs):
    return publish_release(container, 'standalone', *args, **kwargs)


def sf_release(images=None, flavors=None, sync=True):
    '''
    Upload a prebuild makina-states layout in different flavors for various
    distributions to sourceforge.

    For now this includes:

        - lxc container based on Ubuntu LTS
        - current ubuntu LTS based tarball containing the minimum vital
          to bring back to like makina-states without rebuilding it
          totally from scratch. This contains a slimed version of
          the containere files ffrom /salt-venv /srv/*salt /etc/*salt
          /var/log/*salt /var/cache/*salt /var/lib/*salt /usr/bin/*salt*

    this is used in makina-states.cloud.lxc as a base
    for other containers.

    pillar/grain parameters: see mc_cloud_images.settings &
    mc_cloud_images.complete_images to set appropriate parameters
    for git, sourceforce, & etc urls & users

    Do a release::

        mastersalt-call -all mc_lxc.sf_release makina-states-trusty\\
            [flavor=[lxc/standalone]] sync=True|False
    '''
    _s = __salt__
    imgSettings = _s['mc_cloud_images.settings']()
    if isinstance(flavors, basestring):
        flavors = flavors.split(',')
    if isinstance(images, basestring):
        images = images.split(',')
    if not flavors:
        flavors = []
    if images is None:
        images = [a for a in imgSettings['lxc']['images']]
    gret = {'rets': {}, 'result': True}
    if sync:
        mc_lxc.sync_image_reference_containers(
            imgSettings, gret,
            __salt__from_exec=_s,
            _cmd_runner=_run, force=True)
    for img in images:
        imgdata = imgSettings['lxc']['images'][img]
        iflavors = copy.deepcopy(flavors)
        if not iflavors:
            iflavors = copy.deepcopy(imgdata['flavors'])
            # fitler out unsupported flavors ;)
        iflavors = [a for a in iflavors if a in imgdata['flavors']]
        imgret = gret['rets'].setdefault(img, OrderedDict())
        fimgret = imgret.setdefault('flavors', OrderedDict())
        for flavor in iflavors:
            subrets = fimgret.setdefault(flavor, OrderedDict())
            subrets.setdefault('trace', '')
            subrets.setdefault('result', True)
            try:
                for step in [
                    'snapshot',
                    'save_acls',
                    'archive',
                    'upload',
                    'publish_release',
                ]:
                    step_fun = 'mc_cloud_images.{0}_{1}'.format(step, flavor)
                    if step_fun not in __salt__:
                        raise _imgerror(
                            '{2}: no step {0} for {1}'.format(
                                step, flavor, img))
                    subrets[step] = _s[step_fun](img, flavor)
                subrets['result'] = True
            except ImgStepError:
                trace = traceback.format_exc()
                imgret['result'] = False
                gret['result'] = False
                subrets['result'] = False
                subrets['trace'] += '{1}/{2}\n{0}\n'.format(
                    __salt__['mc_utils.magicstring'](trace), flavor, step)
    return gret


clean_lxc_config = mc_lxc.clean_lxc_config


def mount_container(path, **kwargs):
    ret = get_ret(**kwargs)
    _s = __salt__
    mounted = os.path.join(path, 'mounted')
    if not os.path.exists(path):
        os.makedirs(path)
    if not os.path.exists(mounted):
        mret = _s['mount.mount'](path, 'none', fstype='tmpfs')
        if mret is not True:
            raise ImgStepError('lxc: tmpfs wont mount for {0}'.format(path))
        _s['file.touch'](mounted)
        ret['result'] = False
    return ret


def umount_container(path, ret=None, destroy=False, **kwargs):
    ret = get_ret(**kwargs)
    _s = __salt__
    name = os.path.split(path)[-1]
    if os.path.exists(path):
        try:
            if _s['lxc.state'](name) in ['running']:
                cret = ret['umount.lxcstop'] = _s['lxc.stop'](name, kill=True)
                if cret['result'] is True:
                    log.info('{0} has been stopped')
        except Exception:
            ret['result'] = False
        mounts = _s['mount.active'](extended=True)
        if path in mounts:
            cret = ret['umount.lxcumount'] = _s['mount.umount'](path)
            if cret is True:
                log.info('{0} / {1} has been umounted'
                         ' (destroyed if tmpfs)'.format(name, path))
            else:
                ret['result'] = False
    if ret['result'] and destroy:
        shutil.rmtree(path)
    return ret


def guess_template_env(name, clone_from=None):
    if not clone_from:
        clone_from = ''
    data = {}
    os = None
    for i in RELEASES:
        if i in name:
            os = i
            break
    if not os:
        for i in RELEASES:
            if i in clone_from:
                os = i
                break
    if not os:
        os = DEFAULT_OS
    data['os'] = os
    releases = RELEASES[os]
    release = None
    for i in releases['releases']:
        if i in name:
            release = i
            break
    if not release:
        for i in releases['releases']:
            if i in clone_from:
                release = i
                break
    if not release:
        release = releases['default']
    data['release'] = release
    return data


def build_from_lxc(name,
                   clone_from=None,
                   profile=None,
                   network_profile=None,
                   data=None,
                   **kwargs):
    env = guess_template_env(name, clone_from)
    if not clone_from:
        clone_from = '{os}-{release}'.format(**env)
    env = guess_template_env(name, clone_from)
    ret = get_ret(**kwargs)
    if not clone_from:
        raise _imgerror(
            '{0}: choose between create or clone args for your'
            ' container'.format(name), cret=ret)
    _s = __salt__
    if not data:
        data = settings()
    name = "imgbuild-{0}".format(name)
    path = os.path.join('/var/lib/lxc', name)
    rootfs = os.path.join('/var/lib/lxc', name, 'rootfs')
    lxccfg = os.path.join('/var/lib/lxc', name, 'config')
    try:
        if os.path.exists(path):
            raise _imgerror(
                'Temporary container {0} already exists'
                ''.format(name), cret=ret)
        mount_container(path, ret=ret)
        sd = _s['mc_cloud_vm.vt_settings']('lxc')
        ret = {}
        if not profile:
            profile = copy.deepcopy(sd['defaults']['profile'])
        if not network_profile:
            network_profile = copy.deepcopy(sd['defaults']['network_profile'])
        profile['clone_from'] = clone_from
        containers = _s['lxc.ls'](cache=False)
        if clone_from not in containers:
            options = {}
            LXC_TEMPLATES = {}
            template = LXC_TEMPLATES.get(env['os'], env['os'])
            options['release'] = env['release']
            ret['lxc_parent'] = _s['lxc.create'](
                clone_from,
                template=template,
                options=options,
                network_profile=network_profile)
            if not ret['lxc_parent']['result']:
                raise _imgerror(
                    'lxc template {0} failed to init'
                    ''.format(clone_from), cret=ret)
        defaults = sd['defaults']
        ret['lxc'] = _s['lxc.init'](
            name,
            password=_s['mc_utils.generate_password'](32),
            bootstrap_shell=defaults['bootstrap_shell'],
            seed=False,
            profile=profile,
            network_profile=network_profile)
        if not ret['lxc']['result']:
            raise ImgStepError('{0} failed to init'.format(name))
        if _s['lxc.state'](name) != 'running':
            _s['lxc.start'](name)
        rstr = _s['test.rand_str']()
        dest_dir = os.path.join('/srv', rstr)
        bs_ = _s['config.gather_bootstrap_script'](
            bootstrap=defaults['script'])
        for cmd in [
            'mkdir -p {0}'.format(dest_dir),
            'chmod 700 {0}'.format(dest_dir),
        ]:
            if _s['lxc.run_stdout'](name, cmd):
                raise _imgerror(
                    ('tmpdir {0} creation'
                     ' failed ({1}').format(dest_dir, cmd), cret=ret)
        ret['bs_copy'] = _s['lxc.copy_to'](name,
                                           bs_,
                                           '{0}/bootstrap.sh'.format(dest_dir),
                                           makedirs=True)
        if not ret['bs_copy']:
            raise _imgerror(
                'lxc bootstrap script wont transfer in {0}'
                ''.format(name), cret=ret)
        cargs = '-C'
        cargs += ' --local-mastersalt-mode masterless'
        cargs += ' --local-salt-mode masterless'
        cargs += ' --mastersalt 127.0.0.1'
        cmd = ('{0} {2}/bootstrap.sh {1}'
               '').format(defaults['bootstrap_shell'],
                          cargs,
                          dest_dir)
        # log ASAP the forged bootstrap command which can be wrapped
        # out of the output in case of unexpected problem
        log.info('Running {0} in LXC container \'{1}\''
                 .format(cmd, name))
        _s['lxc.wait_started'](name)
        ret['bootstrap'] = _s['lxc.retcode'](name, cmd, output_loglevel='info',
                                             use_vt=True) == 0
        if not ret['bootstrap']:
            raise _imgerror(
                'lxc image build failed {0}'.format(name), cret=ret)
        # shutil.copy2(
        #     '/srv/mastersalt/makina-states/files'
        #     '/sbin/makinastates-snapshot.sh',
        #     rootfs + '/sbin/makinastates-snapshot.sh')
        ret['lxc_stop'] = _s['lxc.stop'](name, kill=True)
        _s['cmd.run_chroot'](
            rootfs,
            'chmod +x {0}'.format('/sbin/makinastates-snapshot.sh'))
        ret['cleanup'] = _s['cmd.run_chroot'](
            rootfs, '/sbin/makinastates-snapshot.sh')
        if ret['cleanup']['retcode']:
            raise _imgerror(
                'lxc snapshot failed: {0}'.format(name), cret=ret)
        ret['acls'] = save_acls_lxc(name)
        with open(lxccfg, 'r') as fic:
            content = fic.read()
        with open(lxccfg, 'w') as fic:
            fic.write(content.replace('imgbuild-', ''))
        ret['tar'] = archive_lxc(container=name,
                                 container_path=path)
    except (ImgError, ImgStepError,) as exc:
        exc.cret = ret
        raise exc
    finally:
        ret['umount'] = umount_container(path, ret=ret, destroy=True)
        if not ret['umount']['result']:
            raise ImgStepError('{0} failed to tear down'.format(name))
    return ret


def get_last_local_lxc_images(name,
                              filtered='.*-standalone.*',
                              clone_from=None,
                              images_path='/var/lib/lxc',
                              template=None):
    env = guess_template_env(name, clone_from)
    candidates = []
    if not template:
        template = 'makina-states-'
        if env['os'] != DEFAULT_OS:
            template += env['os']
        template += '{release}'.format(**env)
    for i in os.listdir(images_path):
        if i.startswith(template) and '.tar' in i:
            candidates.append(i)
    if isinstance(filtered, six.string_types):
        filtered = [filtered]

    def ftr(string):
        for i in filtered:
            if re.search(i, string):
                return False
                break
        return True

    def sortn(i):
        return i
    candidates = filter(ftr, candidates)
    candidates.sort(key=LooseVersion)
    return candidates


def get_last_local_lxc_image(name, clone_from=None, template=None):
    return get_last_local_lxc_images(name,
                                     clone_from=clone_from,
                                     template=template)[-1]


def build_from_docker(img, path=None, **kwargs):
    if path:
        print('path')
    raise saltapi.ImgError('Not implemented')


def build(typs=None, images=None):
    if isinstance(typs, six.string_types):
        typs = typs.split(',')
    if isinstance(images, six.string_types):
        images = images.split(',')
    if not typs:
        typs = [a for a in IMAGES]
    typs = [t for t in typs if t in IMAGES]
    if not images:
        images = []
        for s in typs:
            for img in IMAGES[s]:
                images.append(img)
    rets = {'errors': {}, 'returns': {}, 'result': True}
    for typ in typs:
        for img, data in IMAGES[typ].items():
            if img not in images:
                continue
            fun_ = 'mc_images_helpersbuild_from_{0}'.format(typ)
            try:
                rets['returns'][img] = fun_(img, data)
            except (
                saltapi.ImgError,
            ) as exc:
                rets['result'] = False
                trace = traceback.format_exc()
                rets['errors'][img] = {'exc': '{0}'.format(exc),
                                       'trace': trace}
# vim:set et sts=4 ts=4 tw=80:
