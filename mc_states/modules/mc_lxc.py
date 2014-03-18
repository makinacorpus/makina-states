# -*- coding: utf-8 -*-
'''

.. _module_mc_lxc:

mc_lxc / lxc registry
============================================

This module contains settings for lxc and helper functions

'''

# Import python libs
import logging
import mc_states.utils
from pprint import pformat
import os
import random
import socket
import copy

from mc_states import saltapi
from salt.utils.odict import OrderedDict

_errmsg = saltapi._errmsg
__name = 'lxc'

log = logging.getLogger(__name__)


PROJECT_PATH = 'project/makinacorpus/makina-states'
SFTP_URL = 'frs.sourceforge.net:/home/frs/{0}'.format(PROJECT_PATH)
TARGET = '/var/lib/lxc/makina-states'


def gen_mac():
    return ':'.join(map(lambda x: "%02x" % x, [0x00, 0x16, 0x3E,
                                               random.randint(0x00, 0x7F),
                                               random.randint(0x00, 0xFF),
                                               random.randint(0x00, 0xFF)]))

def is_lxc():
    """
    in case of a container, we have the container name in cgroups
    else, it is equal to /

    in lxc:
        ['11:name=systemd:/user/1000.user/1.session',
        '10:hugetlb:/thisname',
        '9:perf_event:/thisname',
        '8:blkio:/thisname',
        '7:freezer:/thisname',
        '6:devices:/thisname',
        '5:memory:/thisname',
        '4:cpuacct:/thisname',
        '3:cpu:/thisname',
        '2:cpuset:/thisname']

    in host:
        ['11:name=systemd:/',
        '10:hugetlb:/',
        '9:perf_event:/',
        '8:blkio:/',
        '7:freezer:/',
        '6:devices:/',
        '5:memory:/',
        '4:cpuacct:/',
        '3:cpu:/',
        '2:cpuset:/']
    """

    try:
        cgroups = open('/proc/1/cgroup').read().splitlines()
        lxc = not '/' == [a.split(':')[-1]
                          for a in cgroups if ':cpu:' in a][-1]
    except Exception:
        lxc = False
    return lxc


def settings():
    '''Lxc registry

    defaults
        defaults settings to provision lxc containers
        Those are all redefinable at each container level
        ssh_gateway
            ssh gateway info
        ssh_gateway_port
            ssh gateway info
        ssh_gateway_user
            ssh gateway info
        ssh_gateway_key
            ssh gateway info
        size
            default filesystem size for container on lvm
            None
        default_container
            default image
        cron_sync
            activate the img synchronnizer
        cron_hour
            hour for the img synchronnizer
        cron_minute
            minute for the img synchronnizer
        gateway
            '10.5.0.1'
        master
            master to uplink the container to
            None
        master_port
            '4506'
        image
            LXC template to use
            'ubuntu'
        bootsalt_branch
            branch of makina-states to use (prod in prod, dev in dev by default (default_env grain))
        network
            '10.5.0.0'
        netmask
            '16'
        netmask_full
            '255.255.0.0'
        mode
            (salt (default) or mastersalt)
        profile
            default size profile to use (medium) (apply only to lvm)
        profile_type
            default profile type to use (lvm)

                lvm
                    lvm backend from default container
                lvm-scratch
                    lvm backend from default lxc template
                dir
                    dir backend from default container
                dir-scratch
                    dir backend from default lxc template

        bridge
            we install via states a bridge in 10.5/16 lxcbr1)
            'lxcbr1'
        sudo
            True
        use_bridge
            True
        backing
            (lvm, overlayfs, dir, brtfs) 'lvm'
        users
            ['root', 'sysadmin']
        ssh_username
            'ubuntu'
        vgname
            'data'
        lvname
            'data'
        lxc_conf
            []
        lxc_conf_unset'
            []
    containers
        Mapping of containers defintions classified by host
    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        cloudSettings = __salt__['mc_saltcloud.settings']()
        localsettings = __salt__['mc_localsettings.settings']()
        locations = localsettings['locations']
        if 'mastersalt' in cloudSettings['prefix']:
            prefix = '/srv/mastersalt'
        else:
            prefix = '/srv/salt'

        # attention first image here is the default !
        images = OrderedDict()
        images['makina-states-precise'] = {}
        for img in images:
            images[img]['builder_ref'] = '{0}-lxc-ref.foo.net'.format(img)
            md5_file = os.path.join(
                prefix,
                'makina-states/versions/'
                '{0}-lxc_version.txt.md5'.format(img))
            ver_file = os.path.join(
                prefix,
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
        default_container = [a for a in images][0]
        default_containers = OrderedDict()
        # reactivate to provision
        # when you do maintenance
        # default_container:
        maintenance = False
        if maintenance:
            default_containers[grains['id']] = {
                'name': default_container,
                'profile_type': 'dir-scratch',
                'ip': '0.0.0.0',  # set later
                'mode': 'mastersalt',
                'image': 'ubuntu',
                'password': 'ubuntu',
            }
        lxcSettings = __salt__['mc_utils.defaults'](
            'makina-states.services.virt.lxc', {
                'is_lxc': is_lxc(),
                'images_root': '/var/lib/lxc',
                'cron_sync': True,
                'cron_hour': '3',
                'cron_minute': '3',
                'images': images,
                'dnsservers': ['8.8.8.8', '4.4.4.4'],
                'defaults': {
                    'default_container': default_container,
                    'size': None,  # via profile
                    'profile': 'medium',
                    'profile_type': 'lvm',
                    'gateway': '10.5.0.1',
                    'mode': cloudSettings['mode'],
                    'ssh_gateway': None,
                    'ssh_gateway_user': 'root',
                    'ssh_gateway_key': '/root/.ssh/id_dsa',
                    'ssh_gateway_port': None,
                    'master': None,
                    'master_port': '4506',
                    'image': 'ubuntu',
                    'network': '10.5.0.0',
                    'netmask': '16',
                    'bootsalt_branch': cloudSettings['bootsalt_branch'],
                    'netmask_full': '255.255.0.0',
                    'bridge': 'lxcbr1',
                    'sudo': True,
                    'use_bridge': True,
                    'backing': 'lvm',
                    'users': ['root', 'sysadmin'],
                    'ssh_username': 'ubuntu',
                    'vgname': 'lxc',
                    'lvname': None,
                    'lxc_conf': [],
                    'lxc_conf_unset': [],
                },
                'containers': default_containers,
                'lxc_cloud_profiles': {
                    'xxxtrem': {
                        'size': '2000g',
                    },
                    'xxtrem': {
                        'size': '1000g',
                    },
                    'xtrem': {
                        'size': '500g',

                    },
                    'xxxlarge': {
                        'size': '100g',

                    },
                    'xxlarge': {
                        'size': '50g',
                    },
                    'large': {
                        'size': '20g',

                    },
                    'medium': {
                        'size': '10g',
                    },
                    'small': {
                        'size': '5g',
                    },
                    'xsmall': {
                        'size': '3g',
                    },
                    'xxsmall': {
                        'size': '1g',
                    },
                    'xxxsmall': {
                        'size': '500m',
                    },
                },
            }
        )
        lxcSettings['images'] = __salt__['mc_utils.defaults'](
            'makina-states.services.virt.lxc.images',
            lxcSettings['images'])
        if maintenance and (
            '0.0.0.0' ==
            lxcSettings['containers'][
                grains['id']][default_container]['ip']
        ):
            lxcSettings['containers'][
                grains['id']][default_container]['ip'] = (
                '.'.join(
                    lxcSettings['defaults']['network'].split(
                        '.')[:3] + ['2']))
        if not lxcSettings['defaults']['master']:
            lxcSettings['defaults']['master'] = (
                lxcSettings['defaults']['gateway'])
        for target in [t for t in lxcSettings['containers']]:
            # filter dicts and overiddes
            for container in lxcSettings['containers'][target]:
                lxc_data = lxcSettings['containers'][target][container]
                lxc_data['mac'] = __salt__['mc_lxc.find_mac_for_container'](
                    target, container, lxc_data)
                try:
                    socket.gethostbyname(target)
                    # if it is a distant minion
                    if __grains__['id'] != target:
                        lxc_data['ssh_gateway'] = target
                except Exception:
                    pass
                for i in ['ip', 'password']:
                    if not i in lxc_data:
                        raise Exception(
                            'Missing data {1}\n:{0}'.format(i, lxc_data))
                    # shortcut name for profiles
                    # small -> ms-target-small
                    profile_type = lxc_data.get(
                        'profile_type',
                        lxcSettings['defaults']['profile_type'])
                    profile = lxc_data.get('profile',
                                           lxcSettings['defaults']['profile'])
                    if (
                        profile in lxcSettings['lxc_cloud_profiles']
                        and 'profile' in lxc_data
                    ):
                        del lxc_data['profile']
                    if 'dir' in profile_type:
                        sprofile = ''
                        lxc_data['backing'] = 'dir'
                    else:
                        sprofile = '-{0}'.format(profile)
                    lxc_data.setdefault(
                        'profile',
                        __salt__['mc_saltcloud.gen_id'](
                            'ms-{0}{1}-{2}'.format(target,
                                                   sprofile,
                                                   profile_type)))
                lxc_data.setdefault('name', container)
                lxc_data.setdefault('mode', lxcSettings['defaults']['mode'])
                lxc_data.setdefault('size', None)
                lxc_data.setdefault('from_container', None)
                lxc_data.setdefault('snapshot', None)
                if 'mastersalt' in lxc_data.get('mode', 'salt'):
                    default_args = cloudSettings['bootsalt_mastersalt_args']
                else:
                    default_args = cloudSettings['bootsalt_args']
                lxc_data['script_args'] = lxc_data.get('script_args',
                                                       default_args)
                branch = lxc_data.get('bootsalt_branch',
                                      cloudSettings['bootsalt_branch'])
                if (
                    not '-b' in lxc_data['script_args']
                    or not '--branch' in lxc_data['script_args']
                ):
                    lxc_data['script_args'] += ' -b {0}'.format(branch)

                if not 'scratch' in profile_type:
                    lxc_data.setdefault(
                        'from_container',
                        lxcSettings['defaults']['default_container'])
                for i in ["from_container", 'bootsalt_branch',
                          "master", "master_port",
                          "ssh_gateway", "ssh_gateway_port",
                          "ssh_gateway_user", "ssh_gateway_key",
                          'size', 'image', 'bridge', 'netmask', 'gateway',
                          'dnsservers', 'backing', 'vgname', 'lvname',
                          'vgname', 'ssh_username', 'users', 'sudo',
                          'lxc_conf_unset', 'lxc_conf']:
                    lxc_data.setdefault(
                        i,
                        lxcSettings['defaults'].get(i,
                                                    lxcSettings.get(i, None)))
                if 'dir' in profile_type:
                    for k in ['lvname', 'vgname', 'size']:
                        if k in lxc_data:
                            del lxc_data[k]
        return lxcSettings
    return _settings()


def find_mac_for_container(target, container, lxc_data=None):
    '''Generate and assign a mac addess to a specific
    container on a speific host'''
    if not lxc_data:
        lxc_data = {}
    gid = 'makina-states.services.virt.lxc.containerssettings.{1}.{1}.mac'.format(
        target, container)
    mac = lxc_data.get('mac', __salt__['mc_utils.get'](gid, None))
    if not mac:
        __salt__['grains.setval'](gid, gen_mac())
        __salt__['saltutil.sync_grains']()
        mac = __salt__['mc_utils.get'](gid)
        if not mac:
            raise Exception(
                'Error while setting grainmac for {0}/{1}'.format(target,
                                                                  container))
    return mac


def find_ip_for_container(target, container, lxc_data=None):
    '''Search for:

        - an ip in lxc.conf
        - an ip already allocated
        - an random available ip in the range

    THIS IS NOT IMPLEMENTED YET
    '''
    raise Exception('Not implemented')
    if not lxc_data:
        lxc_data = {}
    ip4 = lxc_data.get('ip4', None)
    gid = 'makina-states.services.virt.lxc.containers.{0}.{1}.ip4'.format(
        target, container)
    if not ip4:
        __salt__['grains.setval'](gid, gen_ip4())
        __salt__['saltuitil.sync_grains']()
        ip4 = __salt__['mc_utils.get'](gid)
        if not ip4:
            raise Exception(
                'Error while setting grainip4 for {0}/{1}'.format(target,
                                                              container))
    return ip4


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
#
