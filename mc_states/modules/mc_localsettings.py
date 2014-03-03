# -*- coding: utf-8 -*-
'''

.. _module_mc_localsettings:

mc_localsettings / localsettings variables
============================================
'''

# Import salt libs
import mc_states.utils
import re

__name = 'localsettings'

RVM_URL = (
    'https://raw.github.com/wayneeseguin/rvm/master/binscripts/rvm-installer')


def metadata():
    '''metadata registry for localsettings'''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _metadata():
        return __salt__['mc_macros.metadata'](__name)
    return _metadata()


def _get_ldapVariables(saltmods):
    # see makina-states.services.base.ldap
    return saltmods['mc_utils.defaults'](
        'makina-states.localsettings.ldap', {
            'enabled': False,
            'ldap_uri': 'ldaps://localhost:636/',
            'ldap_base': 'dc=company,dc=org',
            'ldap_passwd': 'ou=People,dc=company,dc=org?sub',
            'ldap_shadow': 'ou=People,dc=company,dc=org?sub',
            'ldap_group': 'ou=Group,dc=company,dc=org?sub',
            'ldap_cacert': ''
        })


def _ldapEn(__salt__):
    return _get_ldapVariables(__salt__).get('enabled', False)


def sort_ifaces(infos):
    a = infos[0]
    key = a
    if re.match('^(eth0)', key):
        key = '100___' + a
    if re.match('^(eth[123456789][0123456789]+\|em|wlan)', key):
        key = '200___' + a
    if re.match('^(lxc\|docker)', key):
        key = '300___' + a
    if re.match('^(veth\|lo)', key):
        key = '900___' + a
    return key


def settings():
    '''settings registry for localsettings

    main_ip
      main server ip
    hostname
      main hostname
    domain
      main domain
    locations
        Well known locations on the filesystem
    rotate
        Default rotation days for logs
    networkManaged
        Do we manage the network configuration
    networkInterfaces
        Dict of configuration for network interfaces
    ldapVariables
        Ldap variables
    ldapEn
        Is pam ldap to be activated
    group
        Group of the special editor group
    groupId
        Gid of the special editor group
    users
        System configured users
    user_keys
        SSH keys tied to users
    keysMappings
        SSH keys tied to users
    cur_pyver
        Current python version
    pythonSettings
        Settings for the python formula
    hosts_list
        Hosts managment lisrt
    makinahosts
        hosts grabbed in pillar
    keyserver
        default GPG server
    debian_stable
        Name of the current debian stable
    ubuntu_lts
        Name of the current ubuntu LTS release
    ubuntu_last
        Name of the last ubuntu release
    debian_mirror
        Default debian mirror
    ubuntu_mirror
        Default ubuntu mirror
    dist
        current system dist
    udist
        current ubuntu dist
    ddist
        current debian dist
    ucomps
        activated comps for ubuntu
    jdkDefaultVer
        default JDK version
    rvmSettings
        RVM related settings
    rvm_url
        rvm download url
    rubies
        Activated rubies
    rvm_user
        RVM user
    rvm_group
        RVM group
    npmSettings
        npm related settings
    SSLSettings
        SSL settings
    locales
        locales to use
    default_locale
        Default locale
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
        data = {}
        saltmods = __salt__  # affect to a var to see further pep8 errors
        pillar = __pillar__
        grains = __grains__
        resolver = saltmods['mc_utils.format_resolve']
        data['sudoers'] = []
        data['sysadmins'] = []
        data['resolver'] = resolver

        data['etckeeper'] = saltmods['mc_utils.defaults'](
            'makina.localsettings.etckeeper', {
                'pm': 'apt',
                'installer': 'dpkg',
                'specialfilewarning': False,
                'autocommit': True,
                'vcs': 'git',
                'commitbeforeinstall': True,
            }
        )

        data['timezoneSettings'] = saltmods['mc_utils.defaults'](
            'makina.localsettings.timezone', {
                'tz': 'Europe/Paris',
            }
        )
        data['grainsPref'] = grainsPref = 'makina-states.localsettings.'
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
        data['locations'] = locations = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.locations', {
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
                'resetperms': (
                    '{prefix}/salt/makina-states/_scripts/reset-perms.py'
                ),
            })
        # logrotation settings
        # This will generate a rotate_variables in the form
        # rotate_variables = {
        #     'days': 31,
        # }
        #
        # include the macro in your states and use:
        #   {{ localsettings.rotate.days }}
        data['rotate'] = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.rotate', {
                'days':  '365',
            })
        # Does the network base config file have to be managed via that
        # See makina-states.localsettings.network
        # Compat for the first test!
        data['networkManaged'] = (
            saltmods['mc_utils.get']('makina-states.network_managed', False)
            or saltmods['mc_utils.get'](grainsPref + 'network.managed', False))
        data['networkInterfaces'] = networkInterfaces = {}
        # lxc configuration has the network configuration inlined in the state
        # and not in pillar
        # it can be also done for other states like this
        for k in pillar:
            if k.endswith('makina-network'):
                networkInterfaces.update(pillar[k])
        # LDAP integration
        data['ldapVariables'] = _get_ldapVariables(saltmods)
        data['ldapEn'] = _ldapEn(saltmods)

        # Editor group to have write permission on salt controlled files
        # but also on project related files
        data['group'] = saltmods['mc_utils.get'](
            grainsPref + 'filesystem.group', 'editor')
        data['groupId'] = saltmods['mc_utils.get'](
            grainsPref + 'filesystem.group_id', '65753')

        # nodejs
        cur_nodejsver = '10.0.26'
        url = 'http://nodejs.org/dist/v{ver}/node-v{ver}-linux-{arch}.tar.gz'
        data['nodejsSettings'] = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.nodejs', {
                'url': url,
                'shas': {
                    'node-v0.10.26-linux-x86.tar.gz': 'b3bebee7f256644266fccce04f54e2825eccbfc0',
                    'node-v0.10.26-linux-x64.tar.gz': 'd15d39e119bdcf75c6fc222f51ff0630b2611160',
                },
                'versions': [cur_nodejsver],
                'version': cur_nodejsver,
                'arch': __grains__['cpuarch'].replace('x86_64', 'x64'),
                'location': locations['apps_dir']+'/node',
            }
        )
        # users data
        data['users'] = users = {}
        data['user_keys'] = user_keys = {}
        data['keysMappings'] = keysMappings = {
            'users': users, 'keys': user_keys}
        cur_pyver = grains['pythonversion']
        if isinstance(cur_pyver, list):
            cur_pyver = '.'.join(['{0}'.format(s) for s in cur_pyver])
        cur_pyver = cur_pyver[:3]
        data['cur_pyver'] = cur_pyver
        data['pythonSettings'] = pythonSettings = saltmods['mc_utils.defaults'](
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
        for sid, cdata in pillar.items():
            if sid.endswith('-makina-users'):
                susers = cdata.get('users', {})
                skeys = cdata.get('keys', {})
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
        data['admin'] = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.admin', {
                'sudoers': [],
                'sysadmin_password': None,
                'root_password': None,
                'sysadmins_keys': []
            }
        )
        if (
            data['admin']['root_password']
            and not data['admin']['sysadmin_keys']
        ):
            data['admin']['sysadmin_password'] = data['admin']['root_password']

        if (
            data['admin']['sysadmin_password']
            and not data['admin']['root_password']
        ):
            data['admin']['root_password'] = data['admin']['sysadmin_password']


        data['defaultSysadmins'] = defaultSysadmins = ['sysadmin']
        if grains['os'] in ['Ubuntu']:
            data['defaultSysadmins'].append('ubuntu')
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
            udata = users[i].copy()
            if i in defaultSysadmins:
                home = udata.get('home',
                                locations['sysadmins_home_dir'] + "/" + i)
            elif i == 'root':
                home = locations['root_home_dir']
            else:
                home = udata.get('home', locations['users_home_dir'] + "/" + i)
            users[i].update({'home': home})

        default_ip = '127.0.0.1'
        ifaces = grains['ip_interfaces'].items()
        ifaces.sort(key=sort_ifaces)
        for iface, ips in ifaces:
            if ips:
                default_ip = ips[0]
                break

        # hosts managment via pillar
        data['makinahosts'] = makinahosts = []
        # main hostname
        domain_parts = __grains__['id'].split('.')
        data['main_ip'] = saltmods['mc_utils.get'](
            grainsPref + 'main_ip', default_ip)
        data['hostname'] = saltmods['mc_utils.get'](
            grainsPref + 'hostname', domain_parts[0])
        default_domain = ''
        if len(domain_parts) > 1:
            default_domain = '.'.join(domain_parts[1:])
        data['domain'] = saltmods['mc_utils.get'](
            grainsPref + 'domain', default_domain)
        data['fqdn'] = saltmods['mc_utils.get']('nickname', __grains__['id'])
        if data['domain']:
            data['makinahosts'].append({
            'ip': '{main_ip}'.format(**data),
            'hosts': '{hostname} {hostname}.{domain}'.format(**data)
            })
        data['hosts_list'] = hosts_list = []
        for k, edata in pillar.items():
            if k.endswith('makina-hosts'):
                makinahosts.extend(edata)

        # -loop to create a dynamic list of hosts based on pillar content
        for host in makinahosts:
            ip = host['ip']
            for dnsname in host['hosts'].split():
                hosts_list.append(ip + ' ' + dnsname)

        # package manager settings
        data['installmode'] = 'latest'
        if __grains__.get('default_env', '') in ['prod']:
            data['installmode'] = 'installed'

        data['keyserver'] = keyserver = 'pgp.mit.edu'
        data['debian_stable'] = debian_stable = 'wheezy'
        data['ubuntu_lts'] = ubuntu_lts = 'precise'
        data['ubuntu_last'] = ubuntu_last = 'saucy'
        data['debian_mirror'] = debian_mirror = saltmods['mc_utils.get'](
            'makina-states.apt.debian.mirror',
            'http://ftp.de.debian.org/debian')

        data['ubuntu_mirror'] = ubuntu_mirror = saltmods['mc_utils.get'](
            'makina-states.apt.ubuntu.mirror',
            'http://ftp.free.fr/mirrors/ftp.ubuntu.com/ubuntu')
        data['dist'] = dist = saltmods['mc_utils.get']('lsb_distrib_codename', '')
        data['udist'] = udist = saltmods['mc_utils.get']('lsb_distrib_codename', ubuntu_lts)
        data['ddist'] = ddist = saltmods['mc_utils.get']('lsb_distrib_codename', debian_stable)
        data['dcomps'] = dcomps = saltmods['mc_utils.get']('makina-states.apt.debian.comps',
                                          'main contrib non-free')
        data['ucomps'] = ucomps = saltmods['mc_utils.get'](
            'makina-states.apt.ubuntu.comps',
            'main restricted universe multiverse')
        if grains['os'] in ['Ubuntu']:
            data['lts_dist'] = ubuntu_lts
        else:
            data['lts_dist'] = debian_stable

        # JDK default version
        data['jdkSettings'] = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.jdk', {
                'default_jdk_ver': 7,
            })
        data['jdkDefaultVer'] = data['jdkSettings']['default_jdk_ver']

        # RVM
        data['rvmSettings'] = rvmSettings = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.rvm', {
                'url': RVM_URL,
                'rubies': ['1.9.3'],
                'user': 'rvm',
                'group': 'rvm'
            })
        data['rvm_url'] = rvm_url = rvmSettings['url']
        data['rubies'] = rubies = rvmSettings['rubies']
        data['rvm_user'] = rvm_user = rvmSettings['user']
        data['rvm_group'] = rvm_group = rvmSettings['group']

        # Node.js
        data['npmSettings'] = npmSettings = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.npm', {
                'packages': [],
                'versions': []
            })
        # SSL settings for reuse in states
        country = saltmods['grains.get']('defaultlanguage')
        if country:
            country = country[:2].upper()
        else:
            country = 'fr'
        data['SSLSettings'] = SSLSettings = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.ssl', {
                'country': country,
                'st': 'Pays de Loire',
                'l': 'NANTES',
                'o': 'NANTES',
                'cn': grains['fqdn'],
                'email': grains['fqdn'],
            })

        # locales
        default_locale = 'fr_FR.UTF-8'
        default_locales = [
            'de_DE.UTF-8',
            'fr_BE.UTF-8',
            'fr_FR.UTF-8',
        ]
        localesdef = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.locales', {
                'locales': default_locales,
                'locale': default_locale,
            }
        )
        data['locales'] = localesdef['locales']
        data['default_locale'] = localesdef['locale']
        # expose any defined variable to the callees
        return data
    return _settings()


def registry():
    '''registry registry for localsettings'''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _registry():
        return __salt__[
            'mc_macros.construct_registry_configuration'
        ](__name, defaults={
            'nscd': {'active': _ldapEn(__salt__)},
            'ldap': {'active': _ldapEn(__salt__)},
            'git': {'active': True},
            'hosts': {'active': True},
            'jdk': {'active': False},
            'etckeeper': {'active': True},
            'locales': {'active': True},
            'localrc': {'active': True},
            'timezone': {'active': True},
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
            'admin': {'active': True},
        })
    return _registry()


def dump():
    return mc_states.utils.dump(__salt__, __name)

#
