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
from salt.utils.odict import OrderedDict
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
        "{data[admin_groups_acls]}"
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
        "{data[admin_groups_acls]}"
        " by dn.base=\"cn=admin,{data[dn]}\" write"
        " by dn.base=\"uid=fd-admin,ou=people,{data[dn]}\" write"
        " by dn.base=\"cn=ldapwriter,ou=virtual,ou=people,{data[dn]}\" read"
        " by anonymous read"
        " by * read"
    ),
    (
        "{{2}}"
        " to attrs=description,telephoneNumber,"
        "roomNumber,gecos,cn,sn,givenname,jpegPhoto"
        "{data[admin_groups_acls]}"
        " by dn.base=\"cn=admin,{data[dn]}\" write"
        " by dn.base=\"uid=fd-admin,ou=people,{data[dn]}\" write"
        " by dn.base=\"cn=ldapwriter,ou=virtual,ou=people,{data[dn]}\" write"
        " by self write"
        " by * read"
    ),
    (
        "{{3}}"
        " to attrs=homePhone,mobile"
        "{data[admin_groups_acls]}"
        " by dn.base=\"cn=admin,{data[dn]}\" write"
        " by dn.base=\"uid=fd-admin,ou=people,{data[dn]}\" write"
        " by dn.base=\"cn=ldapwriter,ou=virtual,ou=people,{data[dn]}\" write"
        " by self write"
        " by * none"
    ),
    (
        "{{4}}"
        " to dn.regex=\"(uid=.*,)?ou=People,{data[dn]}\""
        "{data[admin_groups_acls]}"
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
        "{data[admin_groups_acls]}"
        " by dn.base=\"cn=admin,dc={data[dn]}\" write"
        " by dn.base=\"uid=fd-admin,ou=people,{data[dn]}\" write"
        " by * read"
    ),
    (
        "{{6}}"
        " to dn.subtree=\"ou=people,{data[dn]}\""
        " by dn.base=\"cn=admin,{data[dn]}\" write"
        "{data[admin_groups_acls]}"
        " by dn.base=\"uid=fd-admin,ou=people,{data[dn]}\" write"
        " by dn.base=\"cn=ldapwriter,ou=virtual,ou=people,{data[dn]}\" write"
        " by self write"
        " by * read"
    ),
    (
        "{{7}}"
        " to dn.subtree=\"ou=contact,{data[dn]}\""
        "{data[admin_groups_acls]}"
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
        " to *"
        "{data[admin_groups_acls]}"
        " by dn.base=\"cn=admin,{data[dn]}\" write"
        " by dn.base=\"uid=fd-admin,ou=people,{data[dn]}\" write"
        " by dn.base=\"cn=replicator,ou=virtual,ou=people,{data[dn]}\" read"
        " by * read"
    ),
]


def sync_ldap_quote(k, val):
    if k in ['scope', 'retry', 'searchbase', 'credentials',
               'binddn']:
        val = '"{0}"'.format(val)
    return val


def salt_pw(pw):
    salt = secure_password(8)
    h = hashlib.sha1(pw)
    h.update(salt)
    return encode("{SSHA}" + encode(h.digest() + salt))
    #return "{SSHA}" + encode(h.hexdigest() + salt)
    #return encode("{SSHA}" + encode(h.hexdigest() + salt))
    #return "{SSHA}" + h.hexdigest() + salt
    #return encode( "{SSHA}" + h.hexdigest() + salt)


def sha_pw(pw):
    h = hashlib.sha1(pw)
    return encode("{SHA}" + encode(h.digest()))
    #return "{SHA}" + encode(h.hexdigest())
    #return encode("{SHA}" + encode(h.hexdigest()))
    #return "{SHA}" + h.hexdigest()
    #return encode("{SHA}" + h.hexdigest())


def encode_ldap(k, val):
    s_ = ''
    if not isinstance(val, list):
        val = [val]
    for v in val:
        # chunks = [v[i:i+54].strip() for i in range(0, len(v), 54)]
        ev = ''
        for ix, chunk in enumerate(
            v.strip().encode('base64').splitlines()
        ):
            if ix >= 1:
                ev += ' '
            ev += chunk
            ev += '\n'
        s_ += '\n{0}:: {1}'.format(k, ev)
        # s_ += '\n{0}: {1}'.format(k, '\n'.join(chunks))
        s_ = s_.strip()
    return s_


def order_syncrepl(k):
        if k == '{0}rid':
            i = 0
        else:
            i = 1
        return '{0}_{1}'.format(i, k)


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
            '/etc/ldap/slapd.d/cn=config/olcDatabase={-1}frontend.ldif',
            '/etc/ldap/slapd.d/cn=config/olcDatabase={0}config.ldif',
            '/etc/ldap/slapd.d/cn=config/cn=module{0}.ldif',
        ]
        data = __salt__['mc_utils.defaults'](
            'makina-states.services.dns.slapd', {
                'slapd_directory': "/etc/ldap/slapd.d",
                'extra_dirs': [
                    '/etc/ldap',
                    '/var/lib/ldap',
                ],
                'cn_config_files': [],
                'mode': 'master',
                'writer_groups': ['ldapadministrators'],
                'reader_groups':  ['ldapreaders'],
                'admin_groups_acls': '',
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
                'syncrepl': OrderedDict([
                    ('starttls', "yes"),
                    ('tls_reqcert', "allow"),
                    ('timeout', 3),
                    ('scope', 'sub'),
                    ('retry', "5 5 5 +"),
                    ('type', 'refreshAndPersist'),
                    ('interval', "00:00:04:00")]),
                'olcloglevel': "sync",
                'cert_domain': grains['id'],
                'acls': [],
                'acls_schema': default_acl_schema,
                'master_uri': '',
                'default_schema': True,
                'schemas': [],
                'fd_schema': True})
        data['syncrepl'].setdefault('searchbase', data['dn'])
        local_conf['cn_pass'] = data['config_pw']
        local_conf['dn_pass'] = data['root_pw']
        for k in ['eroot_pw', 'econfig_pw']:
            if not data[k]:
                data[k] = sha_pw(data[k[1:]])
        if not data['root_dn']:
            data['root_dn'] = 'cn=admin,{0}'.format(data['dn'])
        cn_config_files = data['cn_config_files']
        schemas = data['schemas']
        cn_config_files = data['cn_config_files']
        if data['default_schema']:
            for i in [
                '/etc/ldap/slapd.d/cn=config.ldif',
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={0}core.ldif',
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={1}cosine.ldif',
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={2}inetorgperson.ldif'),
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={3}misc.ldif',
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={19}mozilla.ldif',
                '/etc/ldap/slapd.d/cn=config/cn=schema/cn={20}extension.ldif',
            ]:
                if i not in schemas:
                    schemas.append(i)
                if i not in cn_config_files:
                    cn_config_files.append(i)
        for mode, key in {'reader': 'read', 'writer': 'write'}.items():
            for group in data['{0}_groups'.format(mode)]:
                match = 'cn={0},'.format(group)
                if match in data['admin_groups_acls']:
                    continue
                data['admin_groups_acls'] += (
                    " by group.exact=\"cn={0},ou=Group,{data[dn]}\" {1}"
                ).format(group, key, data=data)
        if not data['acls']:
            acls = [a.format(data=data)
                    for a in data['acls_schema'][:]]
            data['acls'] = acls
        s_aclchema = ''
        if data['acls']:
            s_aclchema = encode_ldap('olcAccess', data['acls'])
        data['s_aclchema'] = s_aclchema
        if data['fd_schema']:
            for i in [
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={21}rfc2307bis.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={22}samba.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={23}core-fd.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={24}core-fd-conf.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={25}sudo-fd-conf.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={26}sudo.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={27}service-fd.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={28}systems-fd-conf.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={29}systems-fd.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={30}recovery-fd.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={31}mail-fd-conf.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={32}mail-fd.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={33}gpg-fd.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={34}ldapns.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={35}openssh-lpk.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={36}pgp-keyserver.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={37}pgp-recon.ldif'),
                ('/etc/ldap/slapd.d/cn=config/'
                 'cn=schema/cn={38}pgp-remte-prefs.ldif'),
            ]:
                if i not in schemas:
                    schemas.append(i)
                if i not in cn_config_files:
                    cn_config_files.append(i)
        srepl = ''
        keys = [a for a in data['syncrepl']]
        keys.sort(key=order_syncrepl)
        if data['syncrepl'].get('provider', ''):
            for k in keys:
                val = data['syncrepl'][k]
                srepl += ' {0}={1}'.format(k, sync_ldap_quote(k, val))
                srepl = srepl.strip()
            data['s_syncrepl'] = encode_ldap("olcSyncrepl", srepl)
        __salt__['mc_macros.update_registry_params'](
            'slapd', local_conf, registry_format='pack')
        return data
    return _settings()



#
