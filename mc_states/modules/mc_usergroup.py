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
import logging
import mc_states.utils

__name = 'usergroup'

log = logging.getLogger(__name__)


def settings():
    '''
    usergroup registry

    group
        Group of the special editor group
    groupId
        Gid of the special editor group
    users
        System configured users
    sudoers
        sudoers (project members)
    defaultSysadmins
        Priviliegied local users accounts (sysadmin, ubuntu, vagrant)
    sysadmins_keys
        sysadmins's ssh key to drop inside privilegied accounts
    sysadmin_password
        sysadmin password
    root_password
        root password

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        grains = __grains__
        locations = __salt__['mc_locations.settings']()
        # users data
        data = {}
        data['sudoers'] = []
        data['sysadmins'] = []

        grainsPref = 'makina-states.localsettings.'
        # Editor group to have write permission on salt controlled files
        # but also on project related files
        data['group'] = saltmods['mc_utils.get'](
            grainsPref + 'filesystem.group', 'editor')
        data['groupId'] = saltmods['mc_utils.get'](
            grainsPref + 'filesystem.group_id', '65753')

        # the following part just feed the above users & user_keys variables
        #default  sysadmin settings
        data['admin'] = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.admin', {
                'sudoers': [],
                'sysadmin_password': None,
                'root_password': None,
                'sysadmins_keys': []
            }
        )
        data['admin']['sudoers'] = __salt__['mc_project.uniquify'](
            data['admin']['sudoers'])

        if (
            data['admin']['root_password']
            and not data['admin']['sysadmins_keys']
        ):
            data['admin']['sysadmin_password'] = data['admin']['root_password']

        if (
            data['admin']['sysadmin_password']
            and not data['admin']['root_password']
        ):
            data['admin']['root_password'] = data['admin']['sysadmin_password']

        data['defaultSysadmins'] = defaultSysadmins = ['root', 'sysadmin']
        if grains['os'] in ['Ubuntu']:
            data['defaultSysadmins'].append('ubuntu')
        if saltmods['mc_macros.is_item_active'](
            'nodetypes', 'vagrantvm'
        ):
            defaultSysadmins.append('vagrant')
        root_data = {
            'admin': True,
            'password': data['admin']['root_password'],
            'ssh_keys': data['admin']['sysadmins_keys']
        }
        admin_data = {
            'admin': True,
            'password': data['admin']['sysadmin_password'],
            'ssh_keys': data['admin']['sysadmins_keys'],
        }
        users = data['users'] = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.users', {})
        # default  home
        for i in [a for a in users]:
            udata = users[i].copy()
            if i != 'root' and not i in defaultSysadmins:
                home = udata.get('home', locations['users_home_dir'] + "/" + i)
            users[i].update({'home': home})
        for j in root_data:
            if not 'root' in users:
                users['root'] = {}
            users['root'][j] = root_data[j]
        for i in defaultSysadmins:
            if not i in users:
                users.update({i: admin_data.copy()})
            else:
                for j in admin_data:
                    users[i][j] = admin_data.copy()[j]
        # default  home
        for i in [a for a in users]:
            udata = users[i].copy()
            if i == 'root':
                home = locations['root_home_dir']
            elif i in defaultSysadmins:
                home = udata.get('home',
                                 locations['sysadmins_home_dir'] + "/" + i)
            users[i].update({'home': home})
        return data
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# vim:set et sts=4 ts=4 tw=80:
