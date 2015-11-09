#!/usr/bin/env python
from __future__ import (print_function, division,
                        absolute_import, unicode_literals)
"""
Util to upgrade fusiondirectory schema
stop slapd
remove / update old schemas
add new ones

Then manual work:
    sync the /etc/.../cn=schema directory
    -> makina-states/files/etc/ldap/cn=config/cn=schema

# PREREQUISITES
mkdir /srv/fd
git clone https://github.com/fusiondirectory/fusiondirectory
git clone https://github.com/fusiondirectory/fusiondirectory-plugins.git
git clone https://github.com/fusiondirectory/schema2ldif/
ln -s /srv/fd/schema2ldif/bin/schema2ldif /usr/local/bin/
ln -s /srv/fd/fusiondirectory/contrib/openldap/ /etc/ldap/schema/fusiondirectory
ln -s /srv/fd/fusiondirectory/contrib/bin/fusiondirectory-insert-schema /usr/local/bin/
ln -s /srv/fd/fusiondirectory/contrib/bin/fusiondirectory-setup  /usr/local/bin/
apt-get install libpath-class-perl libnet-ldap-perl libcrypt-cbc-perl libcrypt-unixcrypt-perl libevent-rpc-perl libcrypt-passwdmd5-perl libfile-copy-recursive-perl libxml-twig-perl
mkdir /etc/fusiondirectory

# ON FIRST RUN
vim /etc/fusiondirectory/fusiondirectory.conf
$ED /etc/fusiondirectory/fusiondirectory.conf

# MAY BE DONE AFTER UPGRADE
bin/fusiondirectory-setup --update-cache
bin/fusiondirectory-setup --check-ldap
bin/fusiondirectory-setup --check-config
bin/fusiondirectory-setup --migrate-acls
bin/fusiondirectory-setup --migrate-users

"""
import os
import sys
import re

LDAP_PASSWD = os.environ.get('LDAP_PASSWD', '')
FD_CONTRIB = os.environ.get(
    'FD_CONTRIB',
    '/srv/fd/fusiondirectory/contrib/openldap')
FD_PLUGINS = os.environ.get(
    'FD_PLUGINS', '/srv/fd/fusiondirectory-plugins')
if not LDAP_PASSWD:
    print("set LDAP_PASSWD for cn=admin,cn=config")
if not os.path.exists(FD_CONTRIB):
    print("fd contrib does not exists")
    sys.exit(1)
if not os.path.exists(FD_PLUGINS):
    print("fd plugins does not exists")
    sys.exit(1)

os.chdir(FD_CONTRIB)
slapd_s = '/etc/ldap/slapd.d/cn=config/cn=schema'


def order_schemas(v):
    i = "9999"
    if 'core-fd-conf' in v:
        i = "3999"
    elif 'core-fd' in v:
        i = "2999"
    elif 'gpg-fd' in v:
        i = "9999"
    elif 'ldapns' in v:
        i = "9999"
    elif 'mail-fd-conf' in v:
        i = "8999"
    elif 'mail-fd' in v:
        i = "8999"
    elif 'openssh-lpk' in v:
        i = "9999"
    elif 'pgp-keyserver' in v:
        i = "9999"
    elif 'pgp-recon' in v:
        i = "9999"
    elif 'pgp-remte-prefs' in v:
        i = "9999"
    elif 'recovery-fd' in v:
        i = "5999"
    elif 'rfc2307bis' in v:
        i = "1999"
    elif 'samba' in v:
        i = "1999"
    elif 'service-fd' in v:
        i = "4999"
    elif 'sudo-fd-conf' in v:
        i = "4899"
    elif 'sudo' in v:
        i = "4899"
    elif 'systems-fd-conf' in v:
        i = "4999"
    elif 'systems-fd' in v:
        i = "4999"
    return "{0}_{1}".format(i, v)


def add_schema(ldif, old=None):
    if not old:
        for j in os.listdir(slapd_s):
            if ldif in j:
                old = os.path.join(slapd_s, j)
                break
    if old and os.path.exists(old):
        os.unlink(old)
        print("replacing {0}".format(old))
        with open(old, 'w') as fic:
            with open(ldif) as ldiff:
                fic.write(
                    re.sub('(dn:.*),cn=schema,cn=config', '\\1',
                           ldiff.read(),
                           re.M | re.S | re.U | re.X)
                )
    else:
        new = os.path.join(slapd_s, ldif)
        print("add {0}".format(new))
        with open(new, 'w') as fic:
            with open(ldif) as ldiff:
                fic.write(
                    re.sub('(dn:.*),cn=schema,cn=config', '\\1',
                           ldiff.read(),
                           re.M | re.S | re.U | re.X)
                )
for i in [
    a
    for a in os.listdir('.')
    if (
        'update' not in a
        and 'slapd' not in a
        and a.endswith('schema')
    )
]:
    ldif = i.replace('schema', 'ldif')
    os.system('schema2ldif "{0}">"{1}"'.format(i, ldif))
    add_schema(ldif)
for i in ['gpg', 'ssh', 'sudo', 'mail', 'systems']:
    os.chdir('{0}/{1}/contrib/openldap'.format(FD_PLUGINS, i))
    schemas = [a for a in os.listdir('.') if a.endswith('.schema')]
    for j in schemas:
        ldif = j.replace('schema', 'ldif')
        os.system('schema2ldif "{0}">"{1}"'.format(j, ldif))
        add_schema(ldif)

mv = []
done = []
for i in os.listdir(slapd_s):
    if 'cn=' not in i:
        l = mv
    else:
        l = done
    l.append(i)
numbers = [re.sub('cn={([^}]+)}.*', '\\1', a, re.U | re.S) for a in done]
inumbers = []
for i in numbers:
    try:
        inumbers.append(int(i))
    except Exception:
        pass
if not inumbers:
    inumbers = [0]
counter = max(inumbers)
mv.sort(key=order_schemas)
for i in mv:
    counter += 1
    dest = os.path.join(slapd_s, "cn={{{1}}}{0}".format(i, counter))
    os.rename(os.path.join(slapd_s, i), dest)
for i in os.listdir(slapd_s):
    parts = re.compile('cn={([^}]+)}(.*)\.ldif', re.U | re.S)
    counter = parts.search(i).group(1)
    schema = parts.search(i).group(2)
    content = ''
    fi = os.path.join(slapd_s, i)
    with open(fi) as fic:
        content = fic.read()
    content = re.sub('dn: cn={0}'.format(schema),
                     'dn: cn={{{0}}}{1}'.format(counter, schema),
                     content,
                     re.M | re.S | re.U | re.X)
    content = re.sub('cn: {0}'.format(schema),
                     'cn: {{{0}}}{1}'.format(counter, schema),
                     content,
                     re.M | re.S | re.U | re.X)
    with open(fi, 'w') as fic:
        fic.write(content)

synccmd = ('rsync -av --delete {0}/ '
           '/srv/mastersalt/makina-states/files{0}/').format(slapd_s)
print('running {0}'.format(synccmd))
os.system(synccmd)
#
