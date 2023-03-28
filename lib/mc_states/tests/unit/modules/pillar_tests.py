# -*- coding: utf-8 -*-
import unittest
import copy
from collections import OrderedDict

from .. import base
from mc_states.modules import mc_pillar
from mc_states.modules import mc_utils
from mc_states.modules import mc_macros
from mock import patch, Mock
import yaml
import contextlib

__docformat__ = 'restructuredtext en'


TESTS = {
    'passwords_map': '''
passwords_map:
  a.makina-corpus.net:
    root: uuu
    sysadmin: yyy
    zope: zzz
  b.makina-corpus.net:
    root: ttt
  c.makina-corpus.net:
    sysadmin: xxx
''',
    'ssh_groups': '''
ssh_groups:
  default: [admin, root, sshusers,
            sudo, sysadmin, wheel]
  foo.makina-corpus.net: [ubuntu, git-ro, git-lab]
''',
    'sudoers_map': '''
sudoers_map:
  default: [uuu]
  foo.makina-corpus.net: [sss, ttt]
''',
    'keys_map': '''
keys_map:
  infra:
    - supervision.pub
  sss:
    - sss.pub
  ttt:
    - ttt.pub
  uuu:
    - uuu.pub
  vvv:
    - vvv.pub
''',
    'sysadmins_keys_map': '''
sysadmins_keys_map:
  default: [infra, sss]
  foo.makina-corpus.net: [infra, ttt]
''',
    'mail_configurations': '''
mail_configurations:
  default:
    default_dest: "sysadmin+{id}@makina-corpus.net"
    mode: relay
    auth: true
    smtp_auth:
      mail.makina-corpus.net:
        user: "foo@makina-corpus.net"
        password: bar
    transports:
      '*': mail.makina-corpus.net
    virtual_map:
      - "/root@.*/": "{dest}"
      - "/postmaster@.*/": "{dest}"
      - "/abuse@.*/": "{dest}"
      - "/.*@{id}/": "{dest}"
      - "/.*@localhost/": "{dest}"
      - "/.*@.local/": "{dest}"
  foo.makina-corpus.net:
    transports:
      '*': mail.makina-corpus.tld
''',
    'configurations': '''
configurations:
  foo.makina-corpus.net:
    salt_master: true
    cloud_master: true
    cloud_images:
      makina-states.cloud.images.lxc.images.makina-states-precise:
        builder_ref: bar.makina-corpus.net
  default:
    salt: f.makina-corpus.net
    saltdn: m.makina-corpus.net
    salt_port: 4606
    domain: makina-corpus.net
    salt_master: false
    cloud_master: false
    manage_packages: true
    manage_mails: true
    manage_backups: true
    manage_passwords: true
    manage_ssh_groups: true
    manage_ssh_keys: true
    manage_passwords: true
    manage_sudoers: true
    manage_network: true
    manage_snmpd: true
    manage_hosts: true
    manage_shorewall: true
    manage_fail2ban: true
    manage_ntp_server: false
    backup_mode: burp
    mail_mode: relay
    default_env: prod
    ldap_client: true
'''

}

TEST_NET = '''

non_managed_hosts:
  - o.makina-corpus.net

standalone_hosts:
  - p.makina-corpus.net

cnames:
  testc.makina-corpus.net: testb.makina-corpus.net.
  testb.makina-corpus.net: testa.makina-corpus.net.
  boo.moo: www.foo.fr.
  boo.moo: www.foo.fr.
  foo.moo: a.makina-corpus.net.
  boo.moo.makina-corpus.net: www.foo.fr.
  foo.moo.makina-corpus.net: a.makina-corpus.net.
  goo.moo.makina-corpus.net: a.makina-corpus.net.
  h.makina-corpus.net: b.makina-corpus.net.

rrs_ttls:
  b.makina-corpus.net: 3600

ips_map:
  c.makina-corpus.net: [a.makina-corpus.net]
  goo.moo.makina-corpus.net: [a.makina-corpus.net]
  ns1.makina-corpus.net: [b.makina-corpus.net]
  ns2.makina-corpus.net: [d.makina-corpus.net]
  ns3.makina-corpus.net: [h.makina-corpus.net]


ipsfo_map:
  thisfo.makina-corpus.net: [ifo-online-1.makina-corpus.net]
  a.makina-corpus.net: [ifo-online-1.makina-corpus.net]
  preprod-boo.makina-corpus.net: [ifo-online-1.makina-corpus.net]
  testd.makina-corpus.net: [ifo-online-3.makina-corpus.net]
  preprod-dd.makina-corpus.net: [ifo-online-4.makina-corpus.net]

ips:
  foo.makina-corpus.net: [1.2.3.4]
  a.makina-corpus.net: [1.2.3.5]
  b.makina-corpus.net: [1.2.3.6]
  d.makina-corpus.net: [1.2.3.8]
  e.makina-corpus.net: [1.2.3.9]
  f.makina-corpus.net: [1.2.3.10]
  projecta.makina-corpus.net: [1.2.3.10]
  projectb.makina-corpus.net: [1.2.3.10]
  testa.makina-corpus.net: [1.2.3.10]
  testd.makina-corpus.net: [1.2.3.10]

cloud_vm_attrs:
  preprod-dd.makina-corpus.net:
    domains: [sub.makina-corpus.net]

managed_dns_zones:
  - makina-corpus.com
  - makina-corpus.net
  - makina-corpus.fr
  - makina-corpus.org

ipsfo:
  ifo-online-1.makina-corpus.net: 212.129.4.3
  ifo-online-2.makina-corpus.net: 212.129.4.4
  ifo-online-3.makina-corpus.net: 212.129.4.5
  ifo-online-4.makina-corpus.net: 212.129.4.6

baremetal_hosts:
  - o.makina-corpus.net
  - p.makina-corpus.net
  - foo.makina-corpus.net
  - bar.makina-corpus.net
  - a.makina-corpus.net
  - b.makina-corpus.net
  - d.makina-corpus.net
  - e.makina-corpus.net
  - f.makina-corpus.net
  - testd.makina-corpus.net

vms:
  kvm:
    foo.makina-corpus.net:
      - preprod-goo.makina-corpus.net
  lxc:
    testd.makina-corpus.net:
      - preprod-d.makina-corpus.net
      - preprod-dd.makina-corpus.net
    foo.makina-corpus.net:
      - preprod-moo.makina-corpus.net
      - preprod-boo.makina-corpus.net

dns_serials:
  makina-corpus.net: 2014042221
  makina-corpus.com: 2013042221

dns_servers:
  default:
    master: a.makina-corpus.net
    slaves:
      - ns1: b.makina-corpus.net
      - ns2: d.makina-corpus.net
      - ns3: h.makina-corpus.net
  makina-corpus.eu:
    master: nsbar.makina-corpus.net
    slaves:
      - ns1: nsfoo.makina-corpus.net
  makina-corpus.org: {}
  makina-corpus.net:
    slaves:
      - ns1: h.makina-corpus.net
  makina-corpus.fr:
    slaves:
      - ns1: c.makina-corpus.net
      - ns2: b.makina-corpus.net
  makina-corpus.com:
    slaves:
      - ns1: b.makina-corpus.net

mx_map:
  makina-corpus.com:
    c.makina-corpus.net: {priority: 50}
  makina-corpus.net:
    c.makina-corpus.net: {priority: 50}

rrs_txt:
    - dkim._domainkey.makina-corpus.net:
        - "v=DKIM1; p=Maaa/bb+Kcc/a/fddddeee"
        - "v=DKIM2; p=Maaa/bb+Kcc/a/fddddeee"
    - makina-corpus.net: "v=DKIM1; p=MIGfMAAA/bbbb+Kscccc/CekNeee"
    - dkim._domainkey.makina-corpus.com.com: "v=DKIM1; p=aaa/bbbb+scccc/af/eee"
    - makina-corpus.com.com: "v=DKIM1; p=MIGfMAAA/bbbb+Kscccc/dz/fdddd Neee"

managed_alias_zones: {}

shorewall_overrides:
  foo.makina-corpus.net:
    no_ftp: False
    no_postgresql: False
    params.RESTRICTED_FTP: "foo"
    params.RESTRICTED_POSTGRESQL: "bar"

default_allowed_ips_names:
  default:
    - a.makina-corpus.net
    - b.makina-corpus.net

configurations:
  default:
    manage_ssh_ip_restrictions: false
  preprod-d.makina-corpus.net:
    manage_ssh_ip_restrictions: True

rrs_raw:
  makina-corpus.com:
    - |
      @ SPF "v=spf1 +mx -all"

burp_configurations:
  foo.makina-corpus.net:
    bar.makina-corpus.net:
      cross_filesystem:
        - /var
        - /home
        - /srv
      include:
        - /
'''


class TestCase(base.ModuleCase):

    def test_get_whitel(self):
        def _load():
            return yaml.load(TEST_NET)
        with patch.dict(self.salt, {
            'mc_pillar.loaddb_do': _load,
        }):
            res1 = self._('mc_pillar.whitelisted')('a')
            self.assertEqual(res1, ['1.2.3.5', '1.2.3.6'])

    def test_get_burp_conf(self):
        def _load():
            return yaml.load(TEST_NET)
        with patch.dict(self.salt, {
            'mc_pillar.loaddb_do': _load,
        }):
            res1 = self._('mc_pillar.query')(
                'burp_configurations')['foo.makina-corpus.net']
            self.assertEqual(res1,
                             {'bar.makina-corpus.net': {
                                 'include': ['/'],
                                 'cross_filesystem': [
                                     '/var', '/home', '/srv']}})

    def test_get_shorewallsettings(self):
        def _load():
            data = yaml.load(TEST_NET)
            data['configurations']['default']['manage_firewalld'] = False
            data['configurations']['default']['manage_shorewall'] = True
            return data
        with patch.dict(self.salt, {
            'mc_pillar.loaddb_do': _load
        }):
            res1 = self._('mc_pillar.get_shorewall_settings')(
                'foo.makina-corpus.net')
            res2 = self._('mc_pillar.get_shorewall_settings')(
                'bar.makina-corpus.net')
            self.assertEqual(
                res1['makina-states.services.firewall.shorewall'], True)
            self.assertEqual(
                res2['makina-states.services.firewall.shorewall'], True)
            self.assertEqual(
                res1['makina-states.services.firewall.'
                     'shorewall.params.RESTRICTED_POSTGRESQL'], 'bar')
            self.assertEqual(
                res1['makina-states.services.firewall.'
                     'shorewall.params.RESTRICTED_FTP'], 'foo')
            k = ('makina-states.services.firewall.'
                 'shorewall.params.RESTRICTED_SSH')
            res1 = self._('mc_pillar.get_shorewall_settings')(
                'preprod-dd.makina-corpus.net')
            res2 = self._('mc_pillar.get_shorewall_settings')(
                'preprod-d.makina-corpus.net')
            self.assertEqual('all', res1[k])
            self.assertNotEqual('all', res2[k])

    def test_get_arr(self):
        def _load():
            return yaml.load(TEST_NET)
        with patch.dict(self.salt, {
            'mc_pillar.loaddb_do': _load,
        }):
            res = self._('mc_pillar.rrs_a_for')('makina-corpus.net')
            self.assertEqual(
                res.splitlines(),
                '       a.ifo-online-1.makina-corp'
                'us.net. A 212.129.4.3\n'
                '       a.makina-corpus.net. A 1.2.3.5\n'
                '       b.makina-corpus.net. A 1.2.3.6\n'
                '       c.makina-corpus.net. A 1.2.3.5\n'
                '       d.makina-corpus.net. A 1.2.3.8\n'
                '       e.makina-corpus.net. A 1.2.3.9\n'
                '       f.makina-corpus.net. A 1.2.3.10\n'
                '       failover.a.makina-corpus.net. A 212.129.4.3\n'
                '       failover.testd.makina-corpus.net. A 212.129.4.5\n'
                '       failover.thisfo.makina-corpus.net. A 212.129.4.3\n'
                '       foo.makina-corpus.net. A 1.2.3.4\n'
                '       goo.moo.makina-corpus.net. A 1.2.3.5\n'
                '       h.makina-corpus.net. A 1.2.3.6\n'
                '       ifo-online-1.a.makina-corpus.net. A 212.129.4.3\n'
                '       ifo-online-1.makina-corpus.net. A 212.129.4.3\n'
                '       ifo-online-1.thisfo.makina-corpus.net.'
                ' A 212.129.4.3\n'
                '       ifo-online-2.makina-corpus.net. A 212.129.4.4\n'
                '       ifo-online-3.makina-corpus.net. A 212.129.4.5\n'
                '       ifo-online-3.testd.makina-corpus.net. A 212.129.4.5\n'
                '       ifo-online-4.makina-corpus.net. A 212.129.4.6\n'
                '       ns1.makina-corpus.net. A 1.2.3.6\n'
                '       ns2.makina-corpus.net. A 1.2.3.8\n'
                '       ns3.makina-corpus.net. A 1.2.3.6\n'
                '       preprod-boo.foo.ifo-online-1.makina'
                '-corpus.net. A 212.129.4.3\n'
                '       preprod-boo.ifo-online-1.makin'
                'a-corpus.net. A 212.129.4.3\n'
                '       preprod-boo.makina-corpus.net. A 212.129.4.3\n'
                '       preprod-d.makina-corpus.net. A 1.2.3.10\n'
                '       preprod-dd.ifo-online-4.makina-c'
                'orpus.net. A 212.129.4.6\n'
                '       preprod-dd.makina-cor'
                'pus.net. A 212.129.4.6\n'
                '       preprod-dd.testd.ifo-online-4.makin'
                'a-corpus.net. A 212.129.4.6\n'
                '       preprod-goo.makina-corpus.net. A 1.2.3.4\n'
                '       preprod-moo.makina-corpus.net. A 1.2.3.4\n'
                '       projecta.makina-corpus.net. A 1.2.3.10\n'
                '       projectb.makina-corpus.net. A 1.2.3.10\n'
                '       sub.makina-corpus.net. A 212.129.4.6\n'

                '       testa.makina-corpus.net. A 1.2.3.10\n'
                '       testd.ifo-online-3.makina-corpus.net. A 212.129.4.5\n'
                '       testd.makina-corpus.net. A 1.2.3.10\n'
                '       thisfo.ifo-online-1.makina-corpus.net. A 212.129.4.3\n'
                '       thisfo.makina-corpus.net. A 212.129.4.3'.splitlines())

    def test_get_mx_rr(self):
        def _load():
            return yaml.load(TEST_NET)
        with patch.dict(self.salt, {
            'mc_pillar.loaddb_do': _load,
        }):
            res = self._('mc_pillar.rrs_mx_for')('makina-corpus.com')
            self.assertEqual(res, '       @ IN MX 50 c.makina-corpus.net.')

    def test_get_raw_rr(self):
        def _load():
            return yaml.load(TEST_NET)
        with patch.dict(self.salt, {
            'mc_pillar.loaddb_do': _load,
        }):
            res = self._('mc_pillar.rrs_raw_for')('makina-corpus.com')
            self.assertEqual(res, '       @ SPF "v=spf1 +mx -all"')

    def test_get_cnames_for(self):
        def _load():
            return yaml.load(TEST_NET)
        with patch.dict(self.salt, {
            'mc_pillar.loaddb_do': _load,
        }):
            res = self._('mc_pillar.rrs_cnames_for')('makina-corpus.net')
            self.assertEqual(res,
                             '       boo.moo.makina-corpus.net.'
                             '  CNAME www.foo.fr.\n'
                             '       foo.moo.makina-corpus.net.'
                             '  CNAME a.makina-corpus.net.\n'
                             '       testb.makina-corpus.net.'
                             '  CNAME testa.makina-corpus.net.\n'
                             '       testc.makina-corpus.net.'
                             '  CNAME testb.makina-corpus.net.')
            self.assertEqual(
                self._('mc_pillar.ip_for')('testc.makina-corpus.net'),
                '1.2.3.10')

    def test_get_ns_rr(self):
        def _load():
            data = yaml.load(TEST_NET)
            return data
        with self.patch(
            filtered=['mc.*'],
            kinds=['modules'],
            funcs={
                'modules': {
                    'mc_pillar.loaddb_do': _load,
                }
            }
        ):
            res = self._('mc_pillar.rrs_ns_for')('makina-corpus.net')
            self.assertEqual(res, '       @ IN NS ns1.makina-corpus.net.')
            res = self._('mc_pillar.rrs_ns_for')('makina-corpus.com')
            self.assertEqual(res, '       @ IN NS ns1.makina-corpus.com.')
            ip1 = self._('mc_pillar.ip_for')('ns1.makina-corpus.net')
            ip3 = self._('mc_pillar.ip_for')('ns1.makina-corpus.fr')
            ip2 = self._('mc_pillar.ip_for')('ns2.makina-corpus.fr')
            self.assertEqual(ip1, '1.2.3.6')
            self.assertEqual(ip2, '1.2.3.6')
            self.assertEqual(ip3, '1.2.3.5')

    def test_get_txts_rr(self):
        def _load():
            return yaml.load(TEST_NET)
        with patch.dict(self.salt, {
            'mc_pillar.loaddb_do': _load
        }):
            res = self._('mc_pillar.rrs_txt_for')('makina-corpus.net')
            self.assertEqual(res,
                             '''\
   \
    dkim._domainkey.makina-corpus.net. TXT "v=DKIM1; p=Maaa/bb+Kcc/a/fddddeee"
   \
    dkim._domainkey.makina-corpus.net. TXT "v=DKIM2; p=Maaa/bb+Kcc/a/fddddeee"
       makina-corpus.net. TXT "v=DKIM1; p=MIGfMAAA/bbbb+Kscccc/CekNeee"''')

    def test_get_nss(self):
        def _load():
            return yaml.load(TEST_NET)
        with patch.dict(self.salt, {
            'mc_pillar.loaddb_do': _load,
        }):
            res1 = self._('mc_pillar.get_slaves_for')('a.makina-corpus.net')
            self.assertEqual(res1,
                             {'all': ['b.makina-corpus.net',
                                      'c.makina-corpus.net',
                                      'd.makina-corpus.net',
                                      'h.makina-corpus.net'],
                              'z': OrderedDict([('makina-corpus.com',
                                                 ['b.makina-corpus.net']),
                                                ('makina-corpus.net',
                                                 ['h.makina-corpus.net']),
                                                ('makina-corpus.fr',
                                                 ['c.makina-corpus.net',
                                                  'b.makina-corpus.net']),
                                                ('makina-corpus.org',
                                                 ['b.makina-corpus.net',
                                                  'd.makina-corpus.net',
                                                  'h.makina-corpus.net'])])})
            res1 = self._('mc_pillar.get_slaves_zones_for')('b.makina-corpus.net')
            self.assertEqual(res1,
                             {'makina-corpus.fr': 'a.makina-corpus.net',
                              'makina-corpus.net': 'a.makina-corpus.net',
                              'makina-corpus.org': 'a.makina-corpus.net',
                              'makina-corpus.com': 'a.makina-corpus.net'})
            res1 = self._('mc_pillar.get_nss_for_zone')('makina-corpus.com')
            res2 = self._('mc_pillar.get_nss_for_zone')('makina-corpus.net')
            self.assertEqual(
                res1,
                {'master': 'a.makina-corpus.net',
                 'slaves': OrderedDict([('ns1.makina-corpus.com',
                                         'b.makina-corpus.net')])})
            self.assertEqual(
                res2,
                {'master': 'a.makina-corpus.net',
                 'slaves': OrderedDict([('ns1.makina-corpus.net',
                                         'h.makina-corpus.net')])})
            res = self._('mc_pillar.get_nss')()
            self.assertEqual(
                res,
                {'all': ['a.makina-corpus.net',
                         'b.makina-corpus.net',
                         'c.makina-corpus.net',
                         'd.makina-corpus.net',
                         'h.makina-corpus.net'],
                 'masters': OrderedDict([('a.makina-corpus.net',
                                          ['b.makina-corpus.net',
                                           'h.makina-corpus.net',
                                           'c.makina-corpus.net',
                                           'd.makina-corpus.net'])]),
                 'slaves': OrderedDict([('b.makina-corpus.net',
                                         ['a.makina-corpus.net']),
                                        ('h.makina-corpus.net',
                                         ['a.makina-corpus.net']),
                                        ('c.makina-corpus.net',
                                         ['a.makina-corpus.net']),
                                        ('d.makina-corpus.net',
                                         ['a.makina-corpus.net'])])})

    def atest_load_networkinfra(self):
        def _load():
            return yaml.load(TEST_NET)
        with patch.dict(self.salt, {
            'mc_pillar.loaddb_do': _load,
        }):
            res = self._('mc_pillar.load_network_infrastructure')()
        self.assertEqual(
            res['ips'], {
                'ips': {
                    'a.ifo-online-1.makina-corpus.net': ['212.129.4.3'],
                    'a.makina-corpus.net': ['1.2.3.5'],
                    'b.makina-corpus.net': ['1.2.3.6'],
                    'c.makina-corpus.net': ['1.2.3.5'],
                    'd.makina-corpus.net': ['1.2.3.8'],
                    'e.makina-corpus.net': ['1.2.3.9'],
                    'f.makina-corpus.net': ['1.2.3.10'],
                    'failover.a.makina-corpus.net': ['212.129.4.3'],
                    'failover.thisfo.makina-corpus.net': ['212.129.4.3'],
                    'foo.makina-corpus.net': ['1.2.3.4'],
                    'goo.moo.makina-corpus.net': ['1.2.3.5'],
                    'ifo-online-1.a.makina-corpus.net': ['212.129.4.3'],
                    'ifo-online-1.makina-corpus.net': ['212.129.4.3'],
                    'ifo-online-1.thisfo.makina-corpus.net': ['212.129.4.3'],
                    'ifo-online-2.makina-corpus.net': ['212.129.4.4'],
                    'ns1.makina-corpus.com': ['1.2.3.6'],
                    'ns1.makina-corpus.net': ['1.2.3.6'],
                    'ns2.makina-corpus.com': ['1.2.3.8'],
                    'ns2.makina-corpus.net': ['1.2.3.8'],
                    'preprod-boo.foo.ifo-online-1.makina-corpus.net': [
                        '212.129.4.3'],
                    'preprod-boo.ifo-online-1.makina-corpus.net': [
                        '212.129.4.3'],
                    'preprod-boo.makina-corpus.net': ['212.129.4.3'],
                    'preprod-goo.makina-corpus.net': ['1.2.3.4'],
                    'preprod-moo.makina-corpus.net': ['1.2.3.4'],
                    'projecta.makina-corpus.net': ['1.2.3.10'],
                    'projectb.makina-corpus.net': ['1.2.3.10'],
                    'thisfo.ifo-online-1.makina-corpus.net': ['212.129.4.3'],
                    'thisfo.makina-corpus.net': ['212.129.4.3']
                }})

    def test_get_fqdn_domains(self):
        tests = []
        for i in ['foo',
                  'foo.bar',
                  'foo.bar.org',
                  'foo.bar.org.']:
            tests.append(self._('mc_pillar.get_fqdn_domains')(i))
        self.assertEqual(tests,
                         [[], ['bar'], ['org', 'bar.org'], ['org', 'bar.org']])

    def test_get_mail_configuration(self):
        def _query(t, *a, **kw):
            if t in ['baremetal_hosts',
                     'non_managed_hosts',
                     'vms']:
                return {
                    'baremetal_hosts': ['foo.makina-corpus.net',
                                        'bar.makina-corpus.net']
                }.get(t, {})
            if t in ['ssh_groups',
                     'mail_configurations',
                     'configurations',
                     'configuration',
                     'keys_map',
                     'sysadmins_keys_map',
                     'sudoers_map']:
                return yaml.load(TESTS[t])[t]
        ret1 = {
            'makina-states.services.mail.postfix': True,
            'makina-states.services.mail.postfix.auth': True,
            'makina-states.services.mail.postfix.default_dest': (
                'sysadmin+{id}@makina-corpus.net'),
            'makina-states.services.mail.postfix.mode': 'relay',
            'makina-states.services.mail.postfix.sasl_passwd': [
                {'entry': '[mail.makina-corpus.net]',
                 'password': 'bar',
                 'user': 'foo@makina-corpus.net'}],
            'makina-states.services.mail.postfix.transport': [
                {'nexthop': 'relay:[mail.makina-corpus.tld]'}],
            'makina-states.services.mail.postfix.virtual_map': [
                {'/root@.*/': (
                    'sysadmin+foo.makina-corpus.net@makina-corpus.net')},
                {'/postmaster@.*/': (
                    'sysadmin+foo.makina-corpus.net@makina-corpus.net')},
                {'/abuse@.*/': (
                    'sysadmin+foo.makina-corpus.net@makina-corpus.net')},
                {'/.*@foo.makina-corpus.net/': (
                    'sysadmin+foo.makina-corpus.net@makina-corpus.net')},
                {'/.*@localhost/': (
                    'sysadmin+foo.makina-corpus.net@makina-corpus.net')},
                {'/.*@.local/': (
                    'sysadmin+foo.makina-corpus.net@makina-corpus.net')}]}
        with self.patch(
            filtered=['mc.*'],
            kinds=['modules'],
            funcs={
                'modules': {
                    'mc_pillar.is_salt_managed': Mock(return_value=True),
                    'mc_pillar.query': Mock(side_effect=_query)
                }
            }
        ):
            res1 = self._('mc_pillar.get_mail_conf')('foo.makina-corpus.net')
            res2 = self._('mc_pillar.get_mail_conf')('bar.makina-corpus.net')
            self.assertEqual(res1, ret1)
            p = 'makina-states.services.mail.postfix.transport'
            self.assertEqual(res2[p],
                             [{'nexthop': 'relay:[mail.makina-corpus.net]'}])

    def test_get_configuration(self):
        def _query(t, *a, **kw):
            if t in ['ssh_groups',
                     'configurations',
                     'configuration',
                     'keys_map',
                     'sysadmins_keys_map',
                     'sudoers_map']:
                return yaml.load(TESTS[t])[t]
        with patch.dict(self.salt, {
            'mc_pillar.query': Mock(side_effect=_query)
        }):
            res1 = self._('mc_pillar.get_configuration')(
                'foo.makina-corpus.net')
            res2 = self._('mc_pillar.get_configuration')(
                'bar.makina-corpus.net')
            self.assertEqual(res1,
                             {'backup_mode': 'burp',
                              'cloud_images': {
                                  'makina-states.cloud.images.lxc.'
                                  'images.makina-states-precise': {
                                      'builder_ref': 'bar.makina-corpus.net'}},
                              'cloud_master': True,
                              'default_env': 'prod',
                              'domain': 'makina-corpus.net',
                              'ldap_client': True,
                              'mail_mode': 'relay',
                              'manage_backups': True,
                              'manage_fail2ban': True,
                              'manage_hosts': True,
                              'manage_mails': True,
                              'manage_network': True,
                              'manage_ntp_server': False,
                              'manage_packages': True,
                              'manage_passwords': True,
                              'manage_shorewall': True,
                              'manage_snmpd': True,
                              'manage_ssh_groups': True,
                              'manage_ssh_keys': True,
                              'manage_sudoers': True,
                              'salt': 'f.makina-corpus.net',
                              'salt_master': True,
                              'salt_port': 4606,
                              'saltdn': 'm.makina-corpus.net'})
            self.assertEqual(res2, {
                             'backup_mode': 'burp',
                             'cloud_master': False,
                             'default_env': 'prod',
                             'domain': 'makina-corpus.net',
                             'ldap_client': True,
                             'mail_mode': 'relay',
                             'manage_backups': True,
                             'manage_fail2ban': True,
                             'manage_hosts': True,
                             'manage_mails': True,
                             'manage_network': True,
                             'manage_ntp_server': False,
                             'manage_packages': True,
                             'manage_passwords': True,
                             'manage_shorewall': True,
                             'manage_snmpd': True,
                             'manage_ssh_groups': True,
                             'manage_ssh_keys': True,
                             'manage_sudoers': True,
                             'salt': 'f.makina-corpus.net',
                             'salt_master': False,
                             'salt_port': 4606,
                             'saltdn': 'm.makina-corpus.net'})

    def test_get_passwords(self):
        data = {}

        def _update_local_reg(name, *args, **kw):
            lreg = data.setdefault(name, {})
            lreg.update(args[0])
            return lreg

        def _local_reg(name, *args, **kw):
            lreg = data.setdefault(name, {})
            return lreg

        def _query(t, *a, **kw):
            if t in ['ssh_groups',
                     'passwords_map',
                     'keys_map',
                     'sysadmins_keys_map',
                     'sudoers_map']:
                return yaml.load(TESTS[t])[t]
        with patch.dict(self.salt, {
            'mc_pillar.query': Mock(side_effect=_query),
            'mc_macros.update_local_registry': Mock(
                side_effect=_update_local_reg),
            'mc_macros.get_local_registry': Mock(side_effect=_local_reg)
        }):
            res1 = self._('mc_pillar.get_passwords')('a.makina-corpus.net')
            self.assertEqual(
                res1,
                {'clear': {'root': 'uuu', 'sysadmin': 'yyy', 'zope': 'zzz'},
                 'crypted': {'root':
                             '$6$SALTsalt$RPj4P7Jeoe99lNTqpdGwNVbgZBZX/IZ8yk'
                             'afFG5KbLUID2QHu7mXVyqhuVJ'
                             '7sgWQlXYPiuWQ5616F7iOTjn2t.',
                             'sysadmin':
                             '$6$SALTsalt$ZY42SLY0beqCisahVQdB0jDN0UPYd9s6Q'
                             '8QYmXGgpVsIq.8nhHh8ws9b7ZdLaBnGYngoXIsQ2Q'
                             'pgOPmbdZ9mr.',
                             'zope':
                             '$6$SALTsalt$1xayxQrnfaujJgpZXKiBIZ4Ef54m'
                             'fQdsFoKUhC66sXhEE3jpo6u9BlD81oo/Tx4QnbSu'
                             '0bVD09FWHrSUH91/z1'}})

            res2 = self._('mc_pillar.get_passwords')('b.makina-corpus.net')
            self.assertEqual(
                res2,
                {'clear': {'root': 'ttt', 'sysadmin': 'ttt'},
                 'crypted': {'root':
                             '$6$SALTsalt$.DJtg9kel/TTG8zCAg9bI'
                             '6jwVBdrIAn/bCCQgiaLOVmzrV9zDVamEX'
                             'Ii1vYQb8MjtqgSzHAwaLAVQ/KCOZQ6b1',
                             'sysadmin':
                             '$6$SALTsalt$.DJtg9kel/TTG8zCAg9bI6'
                             'jwVBdrIAn/bCCQgiaLOVmzrV9zDVamEX'
                             'Ii1vYQb8MjtqgSzHAwaLAVQ/KCOZQ6b1'}})
            self.assertFalse('c.makina-corpus.net' in data['passwords_map'])
            self._('mc_pillar.get_passwords')('c.makina-corpus.net')
            self.assertTrue('c.makina-corpus.net' in data['passwords_map'])

    def test_get_sysadmins_keys(self):
        def _query(t, *a, **kw):
            if t in ['baremetal_hosts',
                     'configurations',
                     'non_managed_hosts',
                     'vms']:
                return {
                    'configurations': {},
                    'baremetal_hosts': ['foo.makina-corpus.net',
                                        'bar.makina-corpus.net']}
            if t in [
                'ssh_groups', 'keys_map',
                'sysadmins_keys_map', 'sudoers_map'
            ]:
                return yaml.load(TESTS[t])[t]
        with self.patch(
            filtered=['mc.*'],
            kinds=['modules'],
            funcs={
                'modules': {
                    'mc_pillar.is_salt_managed': Mock(return_value=True),
                    'mc_pillar.query': Mock(side_effect=_query)
                }
            }
        ):
            res1 = self._('mc_pillar.get_sudoers')('foo.makina-corpus.net')
            res2 = self._('mc_pillar.get_sudoers')('bar.makina-corpus.net')
            self.assertEqual(res1, ['sss', 'ttt', 'uuu'])
            self.assertEqual(res2, ['uuu'])

    def test_get_sudoers_map(self):
        def _query(t, *a, **kw):
            if t in ['baremetal_hosts',
                     'non_managed_hosts',
                     'configurations',
                     'vms']:
                return {
                    'configurations': {},
                    'baremetal_hosts': ['foo.makina-corpus.net',
                                        'bar.makina-corpus.net']}
            if t in ['ssh_groups',
                     'keys_map',
                     'sysadmins_keys_map',
                     'sudoers_map']:
                return yaml.load(TESTS[t])[t]
        with self.patch(
            filtered=['mc.*'],
            kinds=['modules'],
            funcs={
                'modules': {
                    'mc_pillar.is_salt_managed': Mock(return_value=True),
                    'mc_pillar.query': Mock(side_effect=_query)
                }
            }
        ):
            res1 = self._('mc_pillar.get_sysadmins_keys')(
                'foo.makina-corpus.net')
            res2 = self._('mc_pillar.get_sysadmins_keys')(
                'bar.makina-corpus.net')
            self.assertEqual(res1, ['supervision.pub', 'ttt.pub'])
            self.assertEqual(res2, ['supervision.pub', 'sss.pub'])

    def test_get_ssh_groups(self):

        def _query(t, *a, **kw):
            if t == 'ssh_groups':
                return yaml.load(TESTS[t])[t]
        with self.patch(
            filtered=['mc.*'],
            kinds=['modules'],
            funcs={
                'modules': {
                    'mc_pillar.is_salt_managed': Mock(return_value=True),
                    'mc_pillar.query': Mock(side_effect=_query)
                }
            }
        ):
            res1 = self._('mc_pillar.get_ssh_groups')('foo.makina-corpus.net')
            res2 = self._('mc_pillar.get_ssh_groups')('bar.makina-corpus.net')
            self.assertEqual(res1,
                             ['ubuntu', 'git-ro', 'git-lab',
                              'admin', 'root', 'sshusers', 'sudo',
                              'sysadmin', 'wheel'])
            self.assertEqual(res2,
                             ['admin', 'root', 'sshusers',
                              'sudo', 'sysadmin', 'wheel'])


if __name__ == '__main__':
    unittest.main()
# vim:set et sts=4 ts=4 tw=80:
