#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
mc_lxc / Spin up LXC containers and attach them to (master)salt
================================================================
'''
__docformat__ = 'restructuredtext en'
from salt.states import postgres_extension as postgres
import difflib



def absent(name, *args, **kw):
    '''Absent wrapper'''
    ret = {'name': '', 'changes': {}, 'result': None, 'comment': ''}


def present(name,
            from_container=None,
            template='ubuntu',
            vgname=None,
            backing=None,
            snapshot=True,
            profile=None,
            fstype=None,
            lvname=None,
            ip=None,
            mac=None,
            size='10G',
            lxc_conf_unset=None,
            lxc_conf=None,
            master=None,
            user='ubuntu',
            password='ubuntu',
            *args, **kw):

    '''
    Provision a single machine:

        - Generate a temporary ssh key / authorized key files
        - Spin up the lxc template container using salt.modules.lxc
          on desired minion
        - Change lxc config option if any to be changed
        - Start and wait for lxc container to be up and ready for ssh
        - Via ssh:

            - Change any root or user password to dest password
            - Run the script with args inside the context of the container using
            - lxc-attach and any providen configuration args

        - Ping the result minion

            - if ok:

                - Remove the authorized key path
                - Restart the container

            - else bailout in error

    name
        Name of the container
    from_container
        Name of an original container if cloned
    profile
        lxc pillar profile
    template
        lxc template if created
    backing
        Backing store type (None, lvm, brtfs)
    vgname
        LVM vgname if any
    snapshot
        Do we use snapshots on cloned filesystems
    lvname
        LVM lvname if any
    fstype
        fstype
    user
        sysadmin user of the container
    password
        sysadmin password of the container
    mac
        mac address to associate
    ip
        ip to link to
    size
        Size of the container
    lxc_conf_unset
        Configuration variables to unset in lxc conf
    lxc_conf
        LXC configuration variables to set in lxc_conf
    master
        Master to link to if any
    password
        password for root and ubuntu
    '''
    changes = {}
    ret = {'name': name, 'changes': changes, 'result': None, 'comment': ''}
    if from_container:
        method = 'clone'
    else:
        method = 'create'
    exists = __salt__['lxc.exists'](name)
    changes['a_creation'] = 'Container already exists'
    if not exists and method == 'clone':
        if not __salt__['lxc.exists'](from_container):
            return {'result': False,
                    'comment': (
                        'container could not be created: {0}, '
                        '{1} does not exists'.format(name,
                                                     from_container))}
        cret = __salt__['lxc.clone'](
            name=name,
            orig=from_container,
            snapshot=snapshot,
            size=size,
            vgname=vgname,
            profile=profile,
        )
        if cret.get('error', ''):
            ret['result'] = False
            ret['comment'] += cret['error'] + '\n'
            changes['a_creation'] = 'Container cloning error'
            return ret
        else:
            exists = cret['created'] or 'already exists' in cret.get('comment', '')
            ret['comment'] += 'Container cloned\n'
            changes['a_creation'] = 'Container cloned'
    if not exists and method == 'create':
        cret = __salt__['lxc.create'](
            name=name,
            template=template,
            profile=profile,
            fstype=fstype,
            vgname=vgname,
            size=size,
            lvname=lvname,
            backing=backing,
        )
        if cret.get('error', ''):
            ret['result'] = False
            ret['comment'] += cret['error'] + '\n'
            changes['a_creation'] = 'Container creation error'
            return ret
        else:
            exists = (
                cret['created']
                or 'already exists' in cret.get('comment', ''))
            ret['comment'] += 'Container created\n'
            changes['a_creation'] = 'Container created'
    lxc_conf_p = '/var/lib/lxc/{0}/config'.format(name)

    with open(lxc_conf_p, 'r') as fic:
        filtered_lxc_conf = []
        for row in lxc_conf:
            if not row:
                continue
            for conf in row:
                filtered_lxc_conf.append((conf, row[conf]))
        changes['b_lxcconf'] = 'lxc.conf is up to date'
        lines = []
        orig_config = fic.read()
        for line in orig_config.splitlines():
            if line.startswith('#') or not line.strip():
                lines.append([line, ''])
            else:
                line = line.split('=')
                index = line.pop(0)
                lines.append((index.strip(), '='.join(line)))
        for k, item in filtered_lxc_conf:
            matched = False
            for idx, line in enumerate(lines[:]):
                if line[0].startswith(k):
                    matched = True
                    lines[idx] = (k, item)
            if not matched:
                lines.append((k, item))
        dest_lxc_conf = []
        # filter unset
        for opt in lxc_conf_unset:
            for line in lines:
                if not line[0].startswith(opt):
                    dest_lxc_conf.append(line)
        conf = ''
        for k, val in dest_lxc_conf:
            if not val:
                conf += '{0}\n'.format(k)
            else:
                conf += '{0} = {1}\n'.format(k.strip(), val.strip())
        if conf != orig_config:
            wfic = open(lxc_conf_p, 'w')
            wfic.write(conf)
            wfic.close()
            changes['b_lxcconf'] = 'lxc.conf saved'
    return ret

# vim:set et sts=4 ts=4 tw=80:
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# vim:set et sts=4 ts=4 tw=80:
