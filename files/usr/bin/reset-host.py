#!/usr/bin/env python
'''
Reset hostname, minion id, saltconf & sshkeys of a Unix host
'''
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import sys
import tempfile
import shutil
import glob
import os
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--origin', required=True)
parser.add_argument('--destination')
parser.add_argument('--makina-states', default='/srv/makina-states')
parser.add_argument('--same-ssh-for-all', action='store_true')
for i in ('files', 'ssh', 'postfix', 'sshd_keys'):
    parser.add_argument(
        '--reset-{0}'.format(i),
        dest='reset_{0}'.format(i),
        default=False,
        action="store_true")
RESET_FILES = {
    'files': [
        '/etc/burp/burp-client-restore.conf',
        '/etc/burp/burp.conf',
        '/etc/fail2ban/fail2ban.conf',
        '/etc/fail2ban/jail.conf',
        '/etc/hostname',
        '/etc/hosts',
        '/etc/mailname',
        '/etc/nginx/sites-available/*.conf',
        '/etc/postfix/main.cf',
        '__MAKINA_STATES__/etc/salt/grains',
        '__MAKINA_STATES__/etc/salt/master',
        '__MAKINA_STATES__/etc/salt/minion',
        '__MAKINA_STATES__/etc/salt/minion.d/*.conf',
        '/var/spool/postfix/etc/hosts',
        '/etc/aliases',
    ],
    'postfix': [
        '/etc/postfix/virtual_alias_maps',
        '/etc/postfix/relay_domains',
    ]}


def rewrite(fp, origin, destination):
    content = ''
    with open(fp) as fic:
        content = fic.read()
    ncontent = content.replace(origin, destination)
    if '.' in destination and '.' in origin:
        dotorigin = origin.split('.')[0]
        dotdst = destination.split('.')[0]
        ncontent = content.replace(dotorigin, dotdst)
    if not content:
        return
    elif content == ncontent:
        print('In place: {0}'.format(fp))
        return
    with open(fp, 'w') as fic:
        print('Rewrite: {0}'.format(fp))
        fic.write(ncontent)
        fic.flush()


def vsystem(cmd):
    print(cmd)
    return os.system(cmd)


def systemwide_sshkeys():
    for key, opt in {
        '/etc/ssh/ssh_host_rsa_key': '-t rsa -b 4096',
        '/etc/ssh/ssh_host_dsa_key': '-t dsa -b 1024',
        '/etc/ssh/ssh_host_ed25519_key': '-t ed25519',
        '/etc/ssh/ssh_host_ecdsa_key': '-t ecdsa'
    }.items():
        if os.path.exists(key):
            os.remove(key)
        cmd = "ssh-keygen -q -N '' -f {0} {1}".format(key, opt)
        vsystem(cmd)


def main(argv=None):
    if not argv:
        argv = sys.argv
    opts = parser.parse_args()
    if not opts.destination:
        opts.destination = opts.origin
    if opts.reset_ssh:
        copies = set()
        for tkey in 'rsa', 'dsa':
            cdt = '/root/.ssh/id_{0}'.format(tkey)
            if os.path.exists(cdt):
                with open(cdt) as f:
                    content = f.read()
                    for ukey in (
                        glob.glob('/home/users/*/.ssh/id_{0}'.format(tkey)) +
                        glob.glob('/home/*/.ssh/id_{0}'.format(tkey))
                    ):
                        with open(ukey) as ef:
                            ucontent = ef.read()
                        if (
                            (ucontent.strip() == content.strip()) or
                            opts.same_ssh_for_all
                        ):
                            copies.add(ukey)
            sshargs = {'rsa': '-t rsa -b 4096', 'dsa': '-t dsa -b 1024'}
            for k in [cdt, '{0}.pub'.format(cdt)]:
                if os.path.exists(k):
                    os.remove(k)
            cmd = "ssh-keygen -q -N '' -f {0} {1}".format(cdt, sshargs[tkey])
            vsystem(cmd)
            for bcopy in copies:
                for copy in [bcopy, '{0}.pub'.format(bcopy)]:
                    with open(copy, 'w') as w:
                        print('{0}: copy of {1}'.format(bcopy, cdt))
                        w.write(content)
        for tkey in 'rsa', 'dsa':
            for cdt in (
                glob.glob('/home/users/*/.ssh/id_{0}'.format(tkey)) +
                glob.glob('/home/*/.ssh/id_{0}'.format(tkey))
            ):
                if cdt in copies:
                    print('{0}: already ssh root key copy'.format(cdt))
                    continue
                for k in [cdt, '{0}.pub'.format(cdt)]:
                    if os.path.exists(k):
                        os.remove(k)
                cmd = ("ssh-keygen -q -N '' -f {0} {1}"
                       "").format(cdt, sshargs[tkey])
                vsystem(cmd)
        opts.reset_sshd_keys = True
    if opts.reset_sshd_keys:
        systemwide_sshkeys()
    if opts.reset_postfix:
        os.system('newaliases')
    if opts.reset_files or opts.reset_postfix:
        for kind, files in RESET_FILES.items():
            for ofg in files:
                fg = ofg.replace('__MAKINA_STATES__', opts.makina_states)
                for fp in glob.glob(fg):
                    if not os.path.exists(fp):
                        continue
                    if opts.reset_files:
                        rewrite(fp, opts.origin, opts.destination)
                    if opts.reset_postfix and (kind == 'postfix'):
                        os.system('postmap {0}'.format(fp))


if __name__ == '__main__':
    main()
# vim:set et sts=4 ts=4 tw=80:
