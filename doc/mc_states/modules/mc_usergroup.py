#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''

.. _module_mc_usergroup:

mc_usergroup / usergroup registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_usergroup

'''
# Import python libs
import os
import logging
import mc_states.api
from copy import deepcopy
import pwd

__name = 'usergroup'

log = logging.getLogger(__name__)



def user_exists(user):
   try:
        home = pwd.getpwnam(user).pw_dir
        return True
   except KeyError:
        return False


def get_default_groups():
    saltmods = __salt__
    data = {}
    # Editor group to have write permission on salt controlled files
    # but also on project related files
    grainsPref = 'makina-states.localsettings.'
    data['group'] = saltmods['mc_utils.get'](
        grainsPref + 'filesystem.group', 'editor')
    data['groupId'] = saltmods['mc_utils.get'](
        grainsPref + 'filesystem.group_id', '65753')
    return data


def get_default_users():
    users = __salt__['mc_utils.defaults'](
        'makina-states.localsettings.users', {})
    for k in [a for a in users]:
        if '.' in k:
            data = users[k]
            user = k.split('.')[0]
            subk = '.'.join(k.split('.')[1:])
            users[user] = {}
            users[user].update({subk: data})
            del users[k]
    return users


def get_default_sysadmins():
    '''
    get_default_sysadmins
    '''
    _g = __grains__
    _s = __salt__
    lreg = __salt__['mc_localsettings.registry']()
    defaultSysadmins = ['root', 'sysadmin']
    if _g['os'] in ['Ubuntu']:
        defaultSysadmins.append('ubuntu')
    if _s['mc_macros.is_item_active'](
        'nodetypes', 'vagrantvm'
    ):
        defaultSysadmins.append('vagrant')
    # if we dont manage users ourselves, only manage sysadmins which already
    # exists
    if not lreg['is']['users']:
        defaultSysadmins = [a for a in defaultSysadmins if user_exists(a)]
    return defaultSysadmins


def get_home(user, home=None, homes=None, not_using_system=False):
    '''get_home'''
    if home:
        return home
    locations = __salt__['mc_locations.settings']()
    defaultSysadmins = get_default_sysadmins()
    if homes is None:
        homes = locations['users_home_dir']
    try:
        if not_using_system:
            raise KeyError()
        home = pwd.getpwnam(user).pw_dir
    except KeyError:
        if user in ['root']:
            home = locations['root_home_dir']
        elif user in defaultSysadmins:
            home = locations['sysadmins_home_dir'] + "/" + user
            home = os.path.join(homes, user)
        else:
            home = homes + "/" + user
    return home


def settings():
    '''
    usergroup registry

    filesystem.group
        Group of the special editor group
    filesystem.groupId
        Gid of the special editor group
    makina-states.localsettings.users
        System configured users
    makina-states.localsettings.admin.sudoers
        sudoers (project members)
    makina-states.localsettings.defaultSysadmins
        Priviliegied local users accounts (sysadmin, ubuntu, vagrant)
    makina-states.localsettings.admin.sysadmins_keys
        sysadmins's ssh key to drop inside privilegied accounts
    makina-states.localsettings.admin.sysadmin_password
        sysadmin password
    makina-states.localsettings.admin.root_password
        root password
    makina-states.localsettings.admin.absent_keys
        list of mappings to feed ssh_auth.absent_keys
        in order to remove ssh keys entries from all
        managed users

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        # users data
        data = {}
        data.update(get_default_groups())
        data['sudoers'] = []
        data['sysadmins'] = []
        sudoers = []
        sysadmins_keys = []
        data['defaultSysadmins'] = get_default_sysadmins()
        # the following part just feed the above users & user_keys variables
        # default  sysadmin settings
        if _s['mc_macros.is_item_active']('nodetypes', 'vagrantvm'):
            sysadmins_keys.append('salt://makina-states/files/ssh/vagrant.pub')
        if _s['mc_nodetypes.is_travis']():
            sudoers.append('travis')
        data['admin'] = _s['mc_utils.defaults'](
            'makina-states.localsettings.admin', {
                'sudoers': [],
                'sysadmin_password': None,
                'root_password': None,
                'sysadmins_keys': sysadmins_keys,
                'absent_keys': []})
        data['admin']['sudoers'] = _s['mc_project.uniquify'](
            data['admin']['sudoers'])
        if (
            data['admin']['root_password'] and
            not data['admin']['sysadmin_password']
        ):
            data['admin']['sysadmin_password'] = data['admin']['root_password']
        if (
            data['admin']['sysadmin_password'] and
            not data['admin']['root_password']
        ):
            data['admin']['root_password'] = data['admin']['sysadmin_password']
        root_data = {'admin': True,
                     'password': data['admin']['root_password']}
        admin_data = {'admin': True,
                      'password': data['admin']['sysadmin_password']}
        default_keys = {'root': data['admin']['sysadmins_keys']}
        if 'sysadmin_keys' in data['admin']:
            for a in data['admin']['sysadmin_keys']:
                if a not in data['admin']['sysadmins_keys']:
                    data['admin']['sysadmins_keys'].append(a)
        users = data['users'] = get_default_users()
        data['sshkeys'] = _s['mc_utils.defaults'](
            'makina-states.localsettings.sshkeys', default_keys)
        # default  home
        root = users.setdefault('root', {})
        root.update(root_data)
        for i in get_default_sysadmins():
            udata = users.setdefault(i, {})
            sdata = deepcopy(admin_data)
            if i != 'root':
                udata.update(sdata)
            keys = data['sshkeys'].setdefault(i, [])
            for k in data['admin']['sysadmins_keys']:
                if k not in keys:
                    keys.append(k)
        for sudoer in data['sudoers']:
            if sudoer not in data['admin']['sudoers']:
                data['admin']['sudoers'].append(sudoer)
        data['sudoers'] = data['admin']['sudoers']
        for sudoer in data['sudoers']:
            sudata = users.setdefault(sudoer, {})
            groups = sudata.setdefault('groups', [])
            for g in ['admin', 'sudo']:
                if g not in groups:
                    groups.append(g)
        for i in [a for a in users]:
            udata = users[i]
            udata.setdefault("groups", [])
            udata.setdefault("system", False)
            udata.setdefault('home',
                             get_home(i, home=udata.get('home', None)))
            ssh_keys = udata.setdefault('ssh_keys', [])
            ssh_absent_keys = udata.setdefault('ssh_absent_keys', [])
            for k in data['admin']['absent_keys']:
                if k not in ssh_absent_keys:
                    ssh_absent_keys.append(deepcopy(k))
            for k in data['sshkeys'].get(i, []):
                if k not in ssh_keys:
                    ssh_keys.append(k)
            udata['ssh_keys'] = []
            for k in ssh_keys:
                if (
                    '://' not in k and
                    k.endswith('.pub') and
                    '/files/' in k
                ):
                    k = 'salt://files/ssh/' + k
                if k not in udata['ssh_keys']:
                    udata['ssh_keys'].append(k)
        return data
    return _settings()
