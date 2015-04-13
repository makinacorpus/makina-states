#!/usr/bin/env python
from __future__ import absolute_import, print_function
'''
.. _module_mc_cloud_images:

mc_cloud_images / cloud images release managment & delivery
===========================================================



Please also have a look at the runner.
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import traceback
import logging
import os
import copy
import yaml
import mc_states.api
import salt.exceptions
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
           '{img}-{flavor}-{ver}.tar.xz')


class ImgError(salt.exceptions.SaltException):
    '''.'''


class ImgStepError(ImgError):
    '''.'''


def _imgerror(msg, cret=None):
    if cret is not None:
        for i in ['stdout', 'stderr']:
            msg += '\n{0}'.format(
                __salt__['mc_utils.magicstring'](cret[i]))
    return ImgStepError(msg)


def complete_images(data):
    root = data['root']
    images = data['lxc'].setdefault('images', OrderedDict())
    images.setdefault('makina-states-trusty', {})
    for img in [i for i in images]:
        defaults = OrderedDict()
        defaults['builder_ref'] = '{0}-lxc-ref.foo.net'.format(img)
        images[img] = __salt__['mc_utils.dictupdate'](defaults, images[img])
        images[img].setdefault('flavors', ['lxc', 'standalone'])
        for flavor in images[img]['flavors']:
            md5_file = os.path.join(root,
                                    ('makina-states/versions/'
                                     '{0}-{1}_version.txt.md5'
                                     '').format(img, flavor))
            ver_file = os.path.join(root,
                                    ('makina-states/versions/'
                                     '{0}-{1}_version.txt'
                                     '').format(img, flavor))
            if (
                not os.path.exists(ver_file)
                and not os.path.exists(md5_file)
            ):
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
    return __salt__['mc_utils.memoize_cache'](
        _do, [id_, limited], {}, cache_key, ttl)


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


def get_vars(container='makina-states-trusty', flavor='standalone'):
    _s = __salt__
    csettings = settings()
    data = {'container': container, 'flavor': flavor}
    data['ver_file'] = (
        '{file_root}/makina-states/versions/{container}-{flavor}_version.txt'
    )
    data['file_root'] = _s['mc_utils.get']('file_roots')['base'][0]
    data['user'] = csettings['sftp_user']
    data['dest'] = '{container}-{flavor}-{next_ver}.tar.xz'
    data['root'] = '/var/lib/lxc'
    data['user'] = csettings['sftp_user']
    data['fdest'] = '{root}/{dest}'
    data['container_p'] = '{root}/{container}'
    data['rootfs'] = '{container_p}/rootfs'
    data['sftp_url'] = csettings['sftp_url']
    data['git_url'] = csettings['git_url']
    data = _s['mc_utils.format_resolve'](data)
    try:
        cur_ver = int(open(data['ver_file']).read().strip())
    except:
        cur_ver = 0
    next_ver = cur_ver + 1
    data['cur_ver'] = cur_ver
    data['next_ver'] = next_ver
    data = _s['mc_utils.format_resolve'](data)
    return data


def save_acls(container, flavor, *args, **kwargs):
    _s = __salt__
    gvars = get_vars(container, flavor)
    aclf = os.path.join(gvars['container_p'], 'acls.txt')
    # all release flavors are releated, so we just check one here
    # and this must be the last one produced
    # if the last one is not present, all flavors will be rebuilt
    log.info('{container}/{flavor}: archiving acls files'.format(**gvars))
    for root in [gvars['rootfs'], gvars['container_p']]:
        cmd = 'getfacl -R . > acls.txt'
        cret = _s['cmd.run_all'](
            cmd, cwd=root, python_shell=True, salt_timeout=60*60)
        if cret['retcode']:
            raise _imgerror(
                '{container}/{flavor}: error with acl'.format(**gvars),
                cret=cret)
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


def save_acls_lxc(container, *args, **kwargs):
    return save_acls(container, 'lxc', *args, **kwargs)


def save_acls_standalone(container, *args, **kwargs):
    return save_acls(container, 'standalone', *args, **kwargs)


def get_ret(**kwargs):
    ret = kwargs.get('ret',
                     {'result': True,
                      'comment':
                      'sucess',
                      'changes': {}})
    return ret


def archive_standalone(container, *args, **kwargs):
    _s = __salt__
    gvars = get_vars(container, 'standalone')
    if os.path.exists(gvars['fdest']):
        log.info('{container}/{flavor}: {fdest} exists'
                 ', delete it to redo'.format(**gvars))
    else:
        try:
            cmd = ('tar cJfp {fdest} '
                   ' etc/cron.d/*salt*'
                   ' etc/logrotate.d/*salt*'
                   ' etc/init.d/mastersalt-*'
                   ' etc/init.d/salt-*'
                   ' etc/init/mastersalt-*'
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
                     'archiving in {fdest}'.format(**gvars))
            cret = _s['cmd.run_all'](
                cmd,
                cwd=gvars['rootfs'],
                python_shell=True,
                env={'XZ_OPT': '-7e'},
                salt_timeout=60*60)
            if cret['retcode']:
                raise _imgerror(
                    '{container}/{flavor}: '
                    'error with compressing {fdest}'.format(**gvars),
                    cret=cret)
        except (Exception,) as exc:
            if os.path.exists(gvars['fdest']):
                os.remove(gvars['fdest'])
                raise exc
    return gvars['fdest']


def archive_lxc(container, *args, **kwargs):
    _s = __salt__
    gvars = get_vars(container, 'lxc')
    if os.path.exists(gvars['fdest']):
        log.info('{container}/{flavor}: {fdest} exists,'
                 ' delete it to redo'.format(**gvars))
    else:
        cmd = ('tar cJfp {fdest} . '
               '--ignore-failed-read --numeric-owner').format(**gvars)
        try:
            log.info('{container}/{flavor}: '
                     'archiving in {fdest}'.format(**gvars))
            cret = _s['cmd.run_all'](
                cmd,
                cwd=gvars['container_p'],
                python_shell=True,
                env={'XZ_OPT': '-7e'},
                salt_timeout=60*60)
            if cret['retcode']:
                raise _imgerror(
                    '{container}/{flavor}: '
                    'error with compressing {fdest}'.format(**gvars),
                    cret=cret)
        except (Exception,) as exc:
            if os.path.exists(gvars['fdest']):
                os.remove(gvars['fdest'])
                raise exc
    return gvars['fdest']


def upload(container, flavor, *args, **kwargs):
    gvars = get_vars(container, flavor)
    _s = __salt__
    if not os.path.exists(gvars['fdest']):
        raise _imgerror(
            '{container}/{flavor}: '
            'release is not done'.format(**gvars))
    failed, cret = False, None
    cmd = ('rsync -avzP {fdest}'
           ' {user}@{sftp_url}/{dest}.tmp').format(**gvars)
    cret = _s['cmd.run_all'](
        cmd, python_shell=True, use_vt=True, salt_timeout=8*60*60)
    if cret['retcode']:
        failed = True
    cmd = ('echo "rename {dest}.tmp {dest}" '
           '| sftp {user}@{sftp_url}').format(**gvars)
    cret = _s['cmd.run_all'](
        cmd, python_shell=True, use_vt=True, salt_timeout=60)
    if cret['retcode']:
        failed = True
    if failed:
        # bindly try to remove the files
        for sufsuf in ['', '.tmp']:
            gvars['sufsuf'] = i
            cmd = ('echo "rm {dest}{sufsuf}" '
                   '| sftp {user}@{sftp_url}').format(**gvars)
            cret = _s['cmd.run_all'](
                cmd, python_shell=True, use_vt=True, salt_timeout=60)
        raise _imgerror(
            '{container}/{flavor}: '
            'error with remote renaming'.format(**gvars),
            cret=cret)
    return '{sftp_url}/{dest}'.format(**gvars)


def upload_standalone(container, *args, **kwargs):
    return upload(container, 'standalone')


def upload_lxc(container, *args, **kwargs):
    return upload(container, 'lxc')


def publish_release(container, flavor, *args, **kwargs):
    _s = __salt__
    gvars = get_vars(container, flavor)
    cmd = "md5sum {fdest} |awk '{{print $1}}'".format(**gvars)
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

        - lxc container based on Ubuntu LTS (trusty)
        - current ubuntu LTS based tarball containing the minimum vital
          to bring back to like makina-states without rebuilding it
          totally from scratch. This contains a slimed version of
          the containere files ffrom /salt-venv /srv/*salt /etc/*salt
          /var/log/*salt /var/cache/*salt /var/lib/*salt /usr/bin/*salt*

    this is used in makina-states.cloud.lxc as a base
    for other containers.

    pillar/grain parameters:

        makina-states.sf user

    Do a release::

        mastersalt-call -all mc_lxc.sf_release
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
    if not gret['result']:
        return gret
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
# vim:set et sts=4 ts=4 tw=80:
