# -*- coding: utf-8 -*-
'''

.. _module_mc_slapd:

mc_slapd / slapd registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_slapd

'''
# Import python libs
import logging
import mc_states.utils
from salt.utils.pycrypto import secure_password
import base64
import getpass
import hashlib
from base64 import urlsafe_b64encode as encode
import os
__name = 'slapd'


log = logging.getLogger(__name__)


default_acl_schema = [
    (
        "{{0}}"
        " to attrs=userPassword,sambaNTPassword,"
        "sambaLMPassword,sambaPwdLastSet,sambaPWDMustChange"
        " by dn.base=\"cn=admin,{data[dn]}\" write"
        " by dn.base=\"uid=fd-admin,ou=people,{data[dn]}\" write"
        " by dn.base=\"cn=ldapwriter,ou=virtual,ou=people,{data[dn]}\" read"
        " by dn.base=\"cn=replicator,ou=virtual,ou=people,{data[dn]}\" read"
        " by dn.base=\"cn=ldapreader,ou=virtual,ou=people,{data[dn]}\" read"
        " by anonymous auth"
        " by self write"
        " by * none"
    ),
    (
        "{{1}}"
        " to attrs=uid,cn,sn,homeDirectory,"
        "uidNumber,gidNumber,memberUid,loginShell,employeeType"
        " by dn.base=\"cn=admin,{data[dn]}\" write  "
        " by dn.base=\"uid=fd-admin,ou=people,{data[dn]}\" write"
        " by dn.base=\"cn=ldapwriter,ou=virtual,ou=people,{data[dn]}\" read"
        " by anonymous read"
        " by * read"
    ),
    (
        "{{2}}"
        " to attrs=description,telephoneNumber,"
        "roomNumber,gecos,cn,sn,givenname,jpegPhoto"
        " by dn.base=\"cn=admin,{data[dn]}\" write"
        " by dn.base=\"uid=fd-admin,ou=people,{data[dn]}\" write"
        " by dn.base=\"cn=ldapwriter,ou=virtual,ou=people,{data[dn]}\" write"
        " by self write  by * read"
    ),
    (
        "{{3}}"
        " to attrs=homePhone,mobile"
        " by dn.base=\"cn=admin,{data[dn]}\" write"
        " by dn.base=\"uid=fd-admin,ou=people,{data[dn]}\" write"
        " by dn.base=\"cn=ldapwriter,ou=virtual,ou=people,{data[dn]}\" write"
        " by self write"
        " by * none"
    ),
    (
        "{{4}}"
        " to dn.regex=\"(uid=.*,)?ou=People,{data[dn]}\""
        " by dn.base=\"cn=admin,{data[dn]}\" write"
        " by dn.base=\"uid=fd-admin,ou=people,dc={data[dn]}\" write"
        " by dn.base=\"cn=ldapwriter,ou=virtual,ou=people,{data[dn]}\" write"
        " by self write"
        " by anonymous read"
        " by * read"
    ),
    (
        "{{5}}"
        " to dn.subtree=\"ou=group,{data[dn]}\""
        " by dn.base=\"cn=admin,dc={data[dn]}\" write"
        " by dn.base=\"uid=fd-admin,ou=people,{data[dn]}\" write"
        " by * read"
    ),
    (
        "{{6}}"
        " to dn.subtree=\"ou=people,{data[dn]}\""
        " by dn.base=\"cn=admin,{data[dn]}\" write"
        " by dn.base=\"uid=fd-admin,ou=people,{data[dn]}\" write"
        " by dn.base=\"cn=ldapwriter,ou=virtual,ou=people,{data[dn]}\" write"
        " by self write"
        " by * read"
    ),
    (
        "{{7}}"
        " to dn.subtree=\"ou=contact,{data[dn]}\""
        " by dn.base=\"cn=admin,{data[dn]}\" write"
        " by dn.base=\"uid=fd-admin,ou=people,{data[dn]}\" write"
        " by dn.base=\"cn=ldapwriter,ou=virtual,ou=people,{data[dn]}\" write"
        " by anonymous none"
        " by dn.one=\"ou=people,{data[dn]}\" read"
        " by * none"
    ),
    (
        "{{8}}"
        " to dn.base=\"{data[dn]}\""
        " by * read"
    ),
    (
        "{{9}}"
        "  to *"
        "  by dn.base=\"cn=admin,{data[dn]}\" write"
        "  by dn.base=\"uid=fd-admin,ou=people,{data[dn]}\" write"
        "  by dn.base=\"cn=replicator,ou=virtual,ou=people,{data[dn]}\" read"
        "  by * read"
    ),
]


def salt_pw(pw):
    salt = secure_password(8)
    h = hashlib.sha1(pw)
    h.update(salt)
    return encode( "{SSHA}" + h.hexdigest() + salt)


def sha_pw(pw):
    h = hashlib.sha1(pw)
    return encode("{SHA}" + h.hexdigest())


def settings():
    '''
    slapd registry

    '''
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        pillar = __pillar__
        locations = __salt__['mc_locations.settings']()
        local_conf = __salt__['mc_macros.get_local_registry'](
            'slapd', registry_format='pack')
        cn_pass = local_conf.setdefault('cn_pass', secure_password(32))
        dn_pass = local_conf.setdefault('dn_pass', secure_password(32))

        cn_config_files = [
            ('/etc/ldap/slapd.d/cn=config/olcDatabase={1}hdb/'
             'olcOverlay={0}memberof.ldif'),
            ('/etc/ldap/slapd.d/cn=config/olcDatabase={1}hdb/'
             'olcOverlay={1}syncprov.ldif'),
            '/etc/ldap/slapd.d/cn=config/cn=schema.ldif',
            '/etc/ldap/slapd.d/cn=config/olcDatabase={1}hdb.ldif',
            #'/etc/ldap/slapd.d/cn=config/olcDatabase={-1}frontend.ldif',
            '/etc/ldap/slapd.d/cn=config/olcDatabase={0}config.ldif',
            '/etc/ldap/slapd.d/cn=config/cn=module{0}.ldif',
        ]
        slapdData = __salt__['mc_utils.defaults'](
            'makina-states.services.dns.slapd', {
                'slapd_directory': "/etc/ldap/slapd.d",
                'extra_dirs': [
                    '/etc/ldap',
                    '/var/lib/ldap',
                ],
                'cn_config_files': [],
                'mode': 'master',
                'pkgs': ['ldap-utils', 'ca-certificates',
                         'slapd', 'python-ldap'],
                'user': 'openldap',
                'group': 'openldap',
                'service_name': 'slapd',
                'SLAPD_CONF': '/etc/ldap/slapd.d',
                'SLAPD_PIDFILE': '',
                'SLAPD_SERVICES': 'ldaps:/// ldap:/// ldapi:///',
                'SLAPD_NO_START': "",
                'SLAPD_SENTINEL_FILE': '/etc/ldap/noslapd',
                'SLAPD_OPTIONS': '',
                'init_ldif': 'salt://makina-states/files/etc/ldap/init.ldif',
                'config_dn': 'cn=config',
                'config_cn': 'config',
                'cn_config_files': cn_config_files,
                'config_rootdn': 'cn=admin,cn=config',
                'config_pw': cn_pass,
                'econfig_pw': '',
                'dn': 'dc=sample,dc=com',
                'verify_client': 'never',
                'root_dn': None,
                'root_pw': dn_pass,
                'eroot_pw': '',
                'loglevel': 'sync',
                'syncprov': True,
                'syncrepl': None,
                'olcloglevel': -1,
                'tls_cacert': '',
                'tls_cert': '',
                'tls_key': '',
                'acls': [],
                'acls_schema': default_acl_schema,
                'master_uri': '',
                'cert_domain': grains['id'],
                'default_schema': True,
                'fd_schema': True,
            })
        local_conf['cn_pass'] = slapdData['config_pw']
        local_conf['dn_pass'] = slapdData['root_pw']
        for k in ['eroot_pw', 'econfig_pw']:
            if not slapdData[k]:
                slapdData[k] = sha_pw(slapdData[k[1:]])
        if not slapdData['root_dn']:
            slapdData['root_dn'] = 'cn=admin,{0}'.format(slapdData['dn'])
        cn_config_files = slapdData['cn_config_files']
        if not slapdData['tls_cert']:
            info = __salt__['mc_ssl.ca_ssl_certs'](slapdData['cert_domain'])[0]
            slapdData['tls_cacert'] = info[0]
            slapdData['tls_cert'] = info[1]
            slapdData['tls_key'] = info[2]
        cn_config_files = slapdData['cn_config_files']
        if slapdData['default_schema']:
            for i in [
                '/etc/ldap/slapd.d/cn=config.ldif',
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={0}core.ldif',
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={1}cosine.ldif',
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={2}inetorgperson.ldif'),
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={3}misc.ldif',
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={4}rfc2307bis.ldif',
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={8}samba.ldif',
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={11}ldapns.ldif',
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={19}mozilla.ldif',
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={15}sudo.ldif',
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={17}openssh-lpk.ldif'),
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={20}extension.ldif',
            ]:
                if i not in cn_config_files:
                    cn_config_files.append(i)
        if not slapdData['acls']:
            acls = [a.format(data=slapdData)
                    for a in slapdData['acls_schema'][:]]
            slapdData['acls'] = acls
        if slapdData['fd_schema']:
            for i in [
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={5}service-fd.ldif',
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={6}systems-fd-conf.ldif'),
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={7}systems-fd.ldif',
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={9}core-fd.ldif',
                ('/etc/ldap/slapd.d/cn=config/cn=schema/'
                 'cn={10}core-fd-conf.ldif'),
                ('/etc/ldap/slapd.d/cn=config/cn=schema/'
                 'cn={12}recovery-fd.ldif'),
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={13}mail-fd.ldif',
                ('/etc/ldap/slapd.d/cn=config/cn=schema/'
                 'cn={14}mail-fd-conf.ldif'),
                ('/etc/ldap/slapd.d/cn=config/cn=schema/'
                 'cn={16}sudo-fd-conf.ldif'),
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={18}gpg-fd.ldif',
            ]:
                if i not in cn_config_files:
                    cn_config_files.append(i)
        __salt__['mc_macros.update_registry_params'](
            'slapd', local_conf, registry_format='pack')
        return slapdData
    return _settings()


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
