#!/usr/bin/env python
'''
.. _module_mc_cloud_images:

mc_cloud_images / cloudcontroller functions
==============================================
'''

__docformat__ = 'restructuredtext en'
# Import python libs
import logging
import os
import yaml
import mc_states.utils

from mc_states import saltapi

from salt.utils.odict import OrderedDict
__name = 'mc_cloud_images'

log = logging.getLogger(__name__)
_errmsg = saltapi._errmsg
PROJECT_PATH = 'project/makinacorpus/makina-states'
SFTP_URL = 'frs.sourceforge.net:/home/frs/{0}'.format(PROJECT_PATH)
TARGET = '/var/lib/lxc/makina-states'


def settings():
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
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        # attention first image here is the default !
        images = OrderedDict()
        cloud_settings = __salt__['mc_cloud_controller.settings']()
        nt_registry = __salt__['mc_nodetypes.registry']()
        sv_registry = __salt__['mc_services.registry']()
        images['makina-states-precise'] = {}
        root = cloud_settings['root']
        for img in images:
            images[img]['builder_ref'] = '{0}-lxc-ref.foo.net'.format(img)
            md5_file = os.path.join(
                root,
                'makina-states/versions/'
                '{0}-lxc_version.txt.md5'.format(img))
            ver_file = os.path.join(
                root,
                'makina-states/versions/'
                '{0}-lxc_version.txt'.format(img))
            if (
                not os.path.exists(ver_file)
                and not os.path.exists(md5_file)
            ):
                continue
            with open(ver_file) as fic:
                images[img]['lxc_tarball_ver'] = fic.read().strip()
            with open(md5_file) as fic:
                images[img]['lxc_tarball_md5'] = fic.read().strip()
            images[img]['lxc_tarball'] = (
                'https://downloads.sourceforge.net/makinacorpus'
                '/makina-states/'
                '{1}-lxc-{0}.tar.xz'
            ).format(images[img]['lxc_tarball_ver'], img)
            images[img]['lxc_tarball_name'] = os.path.basename(
                images[img]['lxc_tarball'])
        cron_sync = True
        if (
            nt_registry['is']['devhost']
            or not sv_registry['is']['cloud.cloud_controller']
            or not sv_registry['is']['cloud.lxc']
        ):
            cron_sync = False
        data = __salt__['mc_utils.defaults'](
            'makina-states.cloud.images', {
                'lxc': {
                    'images_root': '/var/lib/lxc',
                    'images': images,
                    'cron_sync': cron_sync,
                    'cron_hour': '3',
                    'cron_minute': '3',
                }
            })
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)


def sf_release(img='makina-states-precise'):
    '''Upload the makina-states container lxc tarball to sourceforge;
    this is used in makina-states.services.cloud.lxc as a base
    for other containers.

    pillar/grain parameters:

        makina-states.sf user

    Do a release::

        salt-call -all mc_lxc.sf_release
    '''
    _cli = __salt__.get
    ret = {
        'result': True,
        'comment': '',
        'trace': '',
    }
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
        cret = _cli('cmd.run_all')(cmd, cwd=container_p, salt_timeout=60 * 60)
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
            env={'XZ_OPT': '-7e'},
            salt_timeout=60 * 60)
        if cret['retcode']:
            _errmsg(ret, 'error with compressing')
    cmd = 'rsync -avzP {0} {1}@{2}/{3}.tmp'.format(fdest, user, SFTP_URL, dest)
    cret = _cli('cmd.run_all')(cmd, cwd=container_p, salt_timeout=8 * 60 * 60)
    if cret['retcode']:
        return _errmsg(ret, 'error with uploading')
    cmd = 'echo "rename {0}.tmp {0}" | sftp {1}@{2}'.format(dest,
                                                            user,
                                                            SFTP_URL)
    cret = _cli('cmd.run_all')(cmd, cwd=container_p, salt_timeout=60)
    if cret['retcode']:
        _errmsg(ret, 'error with renaming')
    cmd = "md5sum {0} |awk '{{print $1}}'".format(fdest)
    cret = _cli('cmd.run_all')(cmd, cwd=container_p, salt_timeout=60 * 60)
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
    cret = _cli('cmd.run_all')(
        cmd,
        cwd=root + '/makina-states',
        salt_timeout=60)
    if cret['retcode']:
        _errmsg(ret, 'error with commiting new version')
    ret['comment'] = 'release {0} done'.format(next_ver)
    return ret


# vim:set et sts=4 ts=4 tw=80:
