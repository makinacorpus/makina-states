# -*- coding: utf-8 -*-
'''
Salt related variables
============================================

'''

# Import salt libs
import mc_states.utils

__name = 'localsettings'

RVM_URL = (
    'https://raw.github.com/wayneeseguin/rvm/master/binscripts/rvm-installer')


def metadata():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _metadata(registry):
        return __salt__['mc_macros.metadata'](__name)
    return _metadata()


def settings():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings(REG):
        saltmods = __salt__  # affect to a var to see further pep8 errors
        resolver = saltmods['mc_utils.format_resolve']
        metadata = saltmods['mc_{0}.metadata'.format(__name)]()
        pillar = __pillar__
        grains = __grains__
        grainsPref = 'makina-states.localsettings.'
        #-
        # default paths
        # locationsVariables = {
        #     'prefix': '/srv'
        #      ...
        # }
        #
        # include the macro in your states and use:
        #   {{ localsettings.locations.prefix }}
        #
        locations = saltmods['mc_utils.defaults'](
            'makina.localsettings.locations', {
                'root_dir': '/',
                'home_dir': '{root_dir}home',
                'root_home_dir': '{root_dir}root',
                'sysadmins_home_dir': '{home_dir}',
                'users_home_dir': '{home_dir}/users',
                'usr_dir': '{root_dir}usr',
                'share_dir': '{usr_dir}/share',
                'bin_dir': '{usr_dir}/bin',
                'sbin_dir': '{usr_dir}/sbin',
                'venv': '{root_dir}salt-venv',
                'srv_dir': '{root_dir}srv',
                'prefix': '{srv_dir}',
                'rvm_prefix': '{usr_dir}/local',
                'rvm_path': '{rvm_prefix}/rvm',
                'rvm': '{rvm_path}/bin/rvm',
                'vms_docker_root': '{srv_dir}/docker',
                'docker_root': '',
                'lxc_root': '',
                'apps_dir': '{srv_dir}/apps',
                'projects_dir': '{srv_dir}/projects',
                'conf_dir': '{root_dir}etc',
                'initd_dir': '{conf_dir}/init.d',
                'upstart_dir': '{conf_dir}/init',
                'tmp_dir': '{root_dir}tmp',
                'var_dir': '{root_dir}var',
                'var_lib_dir': '{var_dir}/lib',
                'var_spool_dir': '{var_dir}/spool',
                'var_run_dir': '{var_dir}/run',
                'var_log_dir': '{var_dir}/log',
                'var_tmp_dir': '{var_dir}/tmp',
            })
        # logrotation settings
        # This will generate a rotate_variables in the form
        # rotate_variables = {
        #     'days': 31,
        # }
        #
        # include the macro in your states and use:
        #   {{ localsettings.rotate.days }}
        rotate = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.rotate', {
                'days':  '31',
            })
        # Does the network base config file have to be managed via that
        # See makina-states.localsettings.network
        # Compat for the first test!
        networkManaged = (
            saltmods['mc_utils.get']('makina-states.network_managed', False)
            or saltmods['mc_utils.get'](grainsPref + 'network.managed', False))
        networkInterfaces = {}
        # lxc configuration has the network configuration inlined in the state
        # and not in pillar
        # it can be also done for other states like this
        for k in pillar:
            if k.endswith('makina-network'):
                networkInterfaces.update(pillar[k])
        # LDAP integration
        # see makina-states.services.base.ldap
        ldapVariables = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.ldap', {
                'enabled': False,
                'ldap_uri': 'ldaps://localhost:636/',
                'ldap_base': 'dc=company,dc=org',
                'ldap_passwd': 'ou=People,dc=company,dc=org?sub',
                'ldap_shadow': 'ou=People,dc=company,dc=org?sub',
                'ldap_group': 'ou=Group,dc=company,dc=org?sub',
                'ldap_cacert': ''
            })
        ldapEn = ldapVariables.get('enabled', False)

        # Editor group to have write permission on salt controlled files
        # but also on project related files
        group = saltmods['mc_utils.get'](
            grainsPref + 'filesystem.group', 'editor')
        groupId = saltmods['mc_utils.get'](
            grainsPref + 'filesystem.group_id', '65753')

        #  System Users & SSH accces configuration
        #  ----------------------------------------
        #  For system users, we use special pillar entries
        #  suffixed by '-makina-users'
        #  In those entries, we efine a sub mapping with the key 'users'
        #  containing
        #  the users infos
        #  See makina-states.localsettings.vim.
        #  See makina-states.localsettings.users.
        #  See makina-states.localsettings.git
        #
        #  SSH
        #  -----
        #  To allow users to connect as root we define in pillar an entry which
        #  ties #  ssh keys container in the 'keys' mapping to the near by
        #  'users' mapping.
        #  See makina-states.services.base.ssh.
        #
        #  foo-makina-users:
        #    keys:
        #      mpa:
        #        - kiorky.pub
        #    users:
        #      root:
        #        admin: True
        #
        #  bar-makina-users:
        #    toto: {}
        #
        #  ====>
        #
        #  {
        #  'ssh': {'root': {'mpa': ['kiorky.pub']}},
        #  'users': {'root': {'admin': 'True'}, 'toto': {}}
        #  }
        #
        #  - This allows mpa to connect as root which is a super user
        #  - kiorky.pub will be authorized in root's authorized ssh keys
        #  - This will also create root as an admin if not existing
        #  - This will also create a standard user named 'toto'
        users = {}
        user_keys = {}
        keysMappings = {'users': users, 'keys': user_keys}
        cur_pyver = grains['pythonversion']
        if isinstance(cur_pyver, list):
            cur_pyver = '.'.join(['{0}'.format(s) for s in cur_pyver])
        cur_pyver = cur_pyver[:3]
        pythonSettings = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.python', {
                'versions': [cur_pyver],
                'alt_versions': [cur_pyver],
                'version': cur_pyver,
            }
        )
        # filter current version for alt's
        pythonSettings['alt_versions'] = filter(lambda x: x != cur_pyver,
                                                pythonSettings['alt_versions'])

        # the following part just feed the above users & user_keys variables
        ##
        for sid, data in pillar.items():
            if sid.endswith('-makina-users'):
                susers = data.get('users', {})
                skeys = data.get('keys', {})
                for uid, udata in susers.items():
                    # load user keys
                    if not uid in user_keys:
                        user_keys.update({uid: {}})
                    user_key = user_keys[uid]
                    for keyid, keys in skeys.items():
                        if not keyid in user_keys[uid]:
                            user_key.update({keyid: []})
                        for pubkey in keys:
                            if not pubkey in user_key[keyid]:
                                user_key[keyid].append(pubkey)
                    # load user infos by either adding it or updating the
                    # already connected data
                    if uid not in users:
                        users.update({uid: udata})
                    else:
                        u = users[uid]
                        for k, value in udata.items():
                            u.update({k: value})

        #default  sysadmins
        defaultSysadmins = ['sysadmin']
        if saltmods['mc_macros.is_item_active'](
            'makina-states.nodetypes.vagrantvm'
        ):
            defaultSysadmins.append('vagrant')
        for i in defaultSysadmins + ['root']:
            if not i in users:
                users.update({i: {'admin': True}})
            else:
                users[i].update({'admin': True})
        # default  home
        for i in users.keys():
            data = users[i].copy()
            if i in defaultSysadmins:
                home = data.get('home',
                                locations['sysadmins_home_dir'] + "/" + i)
            elif i == 'root':
                home = locations['root_home_dir']
            else:
                home = data.get('home', locations['users_home_dir'] + "/" + i)
            users[i].update({'home': home})

        # hosts managment via pillar
        hosts_list = []
        makinahosts = []
        for k, data in pillar.items():
            if k.endswith('makina-hosts'):
                makinahosts.extend(data)

        # -loop to create a dynamic list of hosts based on pillar content
        for host in makinahosts:
            ip = host['ip']
            for dnsname in host['hosts'].split():
                hosts_list.append(ip + ' ' + dnsname)

        # package manager settings
        keyserver = 'pgp.mit.edu'
        debian_stable = 'wheezy'
        ubuntu_lts = 'precise'
        ubuntu_last = 'saucy'
        debian_mirror = saltmods['mc_utils.get'](
            'makina-states.apt.debian.mirror',
            'http://ftp.de.debian.org/debian')

        ubuntu_mirror = saltmods['mc_utils.get'](
            'makina-states.apt.ubuntu.mirror',
            'http://ftp.free.fr/mirrors/ftp.ubuntu.com/ubuntu')
        dist = saltmods['mc_utils.get']('lsb_distrib_codename', '')
        udist = saltmods['mc_utils.get']('lsb_distrib_codename', ubuntu_lts)
        ddist = saltmods['mc_utils.get']('lsb_distrib_codename', debian_stable)
        dcomps = saltmods['mc_utils.get']('makina-states.apt.debian.comps',
                                          'main contrib non-free')
        ucomps = saltmods['mc_utils.get'](
            'makina-states.apt.ubuntu.comps',
            'main restricted universe multiverse')
        if grains['os'] in ['Ubuntu']:
            lts_dist = ubuntu_lts
        else:
            lts_dist = debian_stable

        # JDK default version
        jdkDefaultVer = '7'

        # RVM
        rvmSettings = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.rvm', {
                'url': RVM_URL,
                'rubies': ['1.9.3'],
                'user': 'rvm',
                'group': 'rvm'
            })
        rvm_url = rvmSettings['url']
        rubies = rvmSettings['rubies']
        rvm_user = rvmSettings['user']
        rvm_group = rvmSettings['group']

        # Node.js
        npmSettings = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.npm', {
                'packages': []
            })

        # SSL settings for reuse in states
        country = saltmods['grains.get']('defaultlanguage')
        if country:
            country = country[:2].upper()
        else:
            country = 'fr'
        SSLSettings = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.ssl', {
                'country': country,
                'st': 'Pays de Loire',
                'l': 'NANTES',
                'o': 'NANTES',
                'cn': grains['fqdn'],
                'email': grains['fqdn'],
            })

        # expose any defined variable to the callees
        return locals()
    return _settings()


def registry():
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _registry(REG):
        settings_reg = __salt__['mc_{0}.settings'.format(__name)]()
        return __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={
            'nscd': {'active': settings_reg['ldapEn']},
            'ldap': {'active': settings_reg['ldapEn']},
            'git': {'active': True},
            'hosts': {'active': True},
            'jdk': {'active': False},
            'locales': {'active': True},
            'localrc': {'active': True},
            'network': {'active': True},
            'nodejs': {'active': False},
            'pkgmgr': {'active': True},
            'python': {'active': False},
            'pkgs': {'active': True},
            'repository_dotdeb': {'active': False},
            'shell': {'active': True},
            'sudo': {'active': True},
            'users': {'active': True},
            'vim': {'active': True},
            'rvm': {'active': False},
        })
    return _registry()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
