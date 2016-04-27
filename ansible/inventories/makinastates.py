#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

'''
MakinaStates custom dynamic inventory script for Ansible, in Python.
'''
import sys
import re
import subprocess
import copy
import argparse
import ConfigParser
import os
import six
import time
import logging
import pprint

re_flags = re.M | re.U | re.S
rei_flags = re.M | re.U | re.S | re.I
TTL_KEY = 'ms_ansible_cache_time'
LIST_TTL_KEY = 'ms_list_ansible_cache_time'
CACHE_CHANGED_KEY = 'ms_ansible_cache_updated'
CACHE_MAX_AGE = 24 * 60 * 60
LIST_CACHE_MAX_AGE = 10 * 60

try:
    import json
except ImportError:
    import simplejson as json


log = logging.getLogger(__name__)


def magic_list_of_strings(hosts=None, separator=',', uniq=True):
    if hosts is None:
        hosts = []
    if isinstance(hosts, basestring):
        hosts = [h.strip() for h in hosts.split()]
    result = []
    for h in hosts:
        for j in h.split(separator):
            if not uniq or (j not in result):
                result.append(j)
    return result


class MakinaStatesInventory(object):

    def __init__(self):
        self.inventory = {'all': {'hosts': []},
                          '_meta': {'hostvars': {}}}
        self.hosts = self.inventory['all']['hosts']
        self.hostvars = self.inventory['_meta']['hostvars']
        self.debug = False
        self.ms = None
        self.cache_path = None
        self.caches = {'list': None, 'hosts': None}
        self.cache_max_age = None
        self.list_cache_age = None
        self.now = time.time()

        self.read_settings()
        self.read_cli_args()
        self.init_cache()
        self.targets = magic_list_of_strings(os.environ.get('ANSIBLE_TARGETS'))

        self.debug = self.args.ms_debug

        # we ask first salt for a valid set of hostnames to get pillar from
        # (minionid == fqdn)
        hosts = self.get_list(refresh=self.args.refresh_cache)

        # if no targets are selected, we compute the whole infrastructure
        # pillar, and this will be long ! (10min on avg inga)
        if self.targets:
            self.targets = [a for a in self.targets if a in hosts]
        else:
            self.targets = [a for a in hosts]

        # we then load the pillars from each host as the salt_pillar hostvar
        # and salt will also fill ansible connexion hostvars as well
        payload = self.load_inventory(self.targets,
                                      refresh=self.args.refresh_cache)
        self.hostvars.update(payload['data'])
        for i in [a for a in self.hostvars]:
            if i not in self.targets:
                self.hostvars.pop(i, None)
        for i in hosts + [a for a in self.hostvars]:
            if i not in self.hosts and i in self.targets:
                self.hosts.append(i)
        self.make_groups()
        self.to_stdout()

    def __debug(self, exit=False, rc=0):
        with open('/foo', 'a') as fic:
            fic.write("--\n")
            fic.write("--\n")
            fic.write("{0}\n".format(pprint.pformat(dict(os.environ))))
            fic.write("--\n")
            fic.write("{0}\n".format(pprint.pformat(sys.argv)))
            fic.write("--\n")
            fic.write("{0}\n".format(self.args.host))
            fic.write("--\n")
            fic.write("{0}\n".format(self.args.list))
            fic.write("--\n")
        if exit:
            sys.exit(rc)

    def make_groups(self):
        listhosts = self.inventory['_meta']['hostvars'].keys()
        mysql = re.compile('mysql', flags=rei_flags)
        pgsql = re.compile('osm|pgsql|postgresql', flags=rei_flags)
        es = re.compile('es|elaticsearch', flags=rei_flags)
        mongo = re.compile('mongo', flags=rei_flags)
        rabbit = re.compile('rabbit', flags=rei_flags)
        solr = re.compile('solr', flags=rei_flags)
        prod = re.compile('^prod-', flags=rei_flags)
        dev = re.compile('^dev-', flags=rei_flags)
        staging = re.compile('^staging-', flags=rei_flags)
        qa = re.compile('^qa-', flags=rei_flags)

        what = {'all': listhosts[:],
                'mysql': filter(lambda x: mysql.search(x), listhosts[:]),
                'pgsql': filter(lambda x: pgsql.search(x), listhosts[:]),
                'rabbit': filter(lambda x: rabbit.search(x), listhosts[:]),
                'solr': filter(lambda x: solr.search(x), listhosts[:]),
                'es': filter(lambda x: es.search(x), listhosts[:]),
                'mongo': filter(lambda x: mongo.search(x), listhosts[:]),
                'prod': filter(lambda x: prod.search(x), listhosts[:]),
                'staging': filter(lambda x: staging.search(x), listhosts[:]),
                'qa': filter(lambda x: qa.search(x), listhosts[:]),
                'dev': filter(lambda x: dev.search(x), listhosts[:])}
        for group, hosts in six.iteritems(what):
            alles = self.inventory.setdefault(group, {})
            alleshosts = alles.setdefault('hosts', [])
            _ = [alleshosts.append(i) for i in hosts  # noqa
                 if i not in alleshosts]
        dns = self.inventory.setdefault('dns', [])
        vms = self.inventory.setdefault('vms', [])
        bms = self.inventory.setdefault('bms', [])
        controllers = self.inventory.setdefault('controllers', [])
        for host, data in six.iteritems(self.inventory['_meta']['hostvars']):
            pillar = data.get('salt_pillar', {})
            if pillar:
                pillar['makinastates_from_ansible'] = True
                is_ = pillar.get('makina-states.cloud', {}).get('is', {})
                mpref = 'makina-states.services.backup.burp.server'
                if pillar.get(mpref, False):
                    self.inventory.setdefault('burp_servers', []).append(host)
                mpref = 'makina-states.services.dns.bind.is_master'
                if pillar.get(mpref, False):
                    self.inventory.setdefault('dns_masters', []).append(host)
                mpref = 'makina-states.services.dns.bind.is_slave'
                if pillar.get(mpref, False):
                    self.inventory.setdefault('dns_slaves', []).append(host)
                if True in [('dns.bind.servers' in a) for a in pillar]:
                    dns.append(host)
                if is_.get('vm', True) and host not in vms:
                    vms.append(host)
                if is_.get('compute_node', True) and host not in bms:
                    bms.append(host)
                if is_.get('controller', True) and host not in controllers:
                    controllers.append(host)

    def fixperms(self):
        if os.path.exists(self.cache_path):
            os.chmod(self.cache_path, 0700)
        for i in self.caches.values():
            if i and os.path.exists(i):
                os.chmod(i, 0o600)

    def init_cache(self):
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)
        self.fixperms()

    def read_settings(self):
        """
        Reads the settings from the etc/ansible.ini file
        """
        config = ConfigParser.SafeConfigParser()
        self.ms = os.path.dirname(
            os.path.dirname(
                os.path.dirname(os.path.realpath(__file__))))
        config.read(self.ms + '/etc/ansible.ini')
        try:
            self.cache_path = config.get('ansible', 'cache_path')
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            self.cache_path = self.ms + '/var/ansible'
        try:
            self.cache_max_age = config.getint('ansible', 'cache_max_age')
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            self.cache_max_age = CACHE_MAX_AGE
        try:
            self.list_cache_max_age = config.getint(
                'ansible', 'list_cache_max_age')
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            self.list_cache_max_age = LIST_CACHE_MAX_AGE
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)
        self.caches = {
            'hosts': self.cache_path + "/ansible-makinastates.cache",
            'list': self.cache_path + "/list_ansible-makinastates.cache"}

    def write_to_cache(self, data, filename):
        """
        Writes data in JSON format to a file
        """
        # when saving to cache, force changed to False
        data = copy.deepcopy(data)
        data[CACHE_CHANGED_KEY] = False
        json_data = self.json_format_dict(data, True)
        with open(filename, 'w') as cache:
            cache.write(json_data)
            cache.close()
        self.fixperms()

    def is_cache_valid(self, entry, ttl_key=TTL_KEY):
        """
        Determines if the cache files have expired, or if it is still valid
        """
        ttls = {TTL_KEY: self.cache_max_age,
                LIST_TTL_KEY: self.list_cache_max_age}
        expired = self.now - (ttls.get(ttl_key, ttls[TTL_KEY]) + 100)
        if (
            isinstance(entry, dict) and
            (entry.get(ttl_key, expired) + self.cache_max_age) > self.now
        ):
            return True
        return False

    def sanitize_payload(self, payload, write=True):
        '''
        - sanitize payload form in form
            {'data': {entrie_n: {ttl_key: XXX, a: YYY}}}
        - Purge expired entries
        Write back in case of cache purge
        '''
        has_changed = False
        if isinstance(payload, dict):
            if 'data' not in payload:
                has_changed = True
            data = payload.setdefault('data', {})
            for k in [a for a in data]:
                iwrite = write
                val = data[k]
                if not isinstance(val, dict):
                    continue
                ttl = val.setdefault(TTL_KEY, self.now)
                if not self.is_cache_valid(val):
                    data.pop(k, None)
                    iwrite = True
                has_changed = ((iwrite and True) or
                               (ttl == self.now) or
                               has_changed)
        else:
            raise TypeError('payload must be a dict')
        payload[CACHE_CHANGED_KEY] = has_changed
        return payload

    def call_salt(self, cmd):
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.ms)
        stdout, stderr = process.communicate()
        ret = process.wait()
        if ret != 0:
            cargs = (stdout, stderr, ret, cmd)
            try:
                msg = ('Something gone wrong with extpillar generation\n'
                       'cmd: {3}\nrc: {2}\n{0}\n{1}').format(*cargs)
            except Exception:
                try:
                    msg = ('Something gone wrong with extpillar generation\n'
                           'cmd: {3}').format(*cargs)
                except Exception:
                    msg = 'Something gone wrong with extpillar generation'
            raise Exception(msg)
        res = json.loads(stdout)
        if isinstance(res, dict) and [a for a in res] == ['local']:
            res = res['local']
        return res

    def get_list(self, refresh=False):
        cmd = 'bin/salt-call --out=json mc_remote_pillar.get_hosts'
        data = {}
        if os.path.exists(self.caches['list']) and not refresh:
            with open(self.caches['list']) as fic:
                try:
                    data = json.loads(fic.read())
                except ValueError:
                    pass
            if not isinstance(data, dict):
                data = {}
            if 'data' not in data and LIST_TTL_KEY not in data:
                data = {}
            if not self.is_cache_valid(data, ttl_key=LIST_TTL_KEY):
                data = {}
        if not data:
            res = self.call_salt(cmd)
            data = {LIST_TTL_KEY: time.time(), 'data': res}
            with open(self.caches['list'], 'w') as fic:
                fic.write(self.json_format_dict(data, pretty=True))
            self.fixperms()
        return data['data']

    def get_ext_pillar(self, hosts=None):
        cmd = ('bin/salt-call --out=json'
               ' mc_remote_pillar.generate_ansible_roster')
        if hosts:
            if isinstance(hosts, list):
                hosts = ','.join(hosts)
            cmd += ' {0}'.format(hosts)
        res = self.call_salt(cmd)
        return res

    def sanitize_and_save(self, payload, force=True):
        payload = self.sanitize_payload(payload)
        if payload.setdefault(CACHE_CHANGED_KEY, force):
            self.write_to_cache(payload, self.caches['hosts'])
        return payload

    def load_inventory(self, hosts, refresh=False):
        """
        Reads the index from the cache file sets self.index
        """
        self.fixperms()
        payload = {}
        if os.path.isfile(self.caches['hosts']) and not refresh:
            if self.debug:
                print('Using {0} cached data, remove the file to use uncached'
                      ' data'.format(self.caches['hosts']))
            with open(self.caches['hosts'], 'r') as cache:
                json_inventory = cache.read()
                try:
                    payload = self.sanitize_payload(
                        json.loads(json_inventory))
                except ValueError:
                    payload = self.sanitize_payload({})
            hosts = [a for a in hosts if a not in payload['data']]
        else:
            payload = self.sanitize_payload(payload)
        if hosts:
            payload = self.update_cache(payload, hosts=hosts)
        return payload

    def update_cache(self, payload, hosts=None):
        """
        Make calls to cobbler and save the output in a cache
            hosts: list of hosts to get pillar from
        """
        if self.debug:
            print('Computing global salt cache, please wait '
                  'it can take several minutes')
        hosts = magic_list_of_strings(hosts)
        data = payload.setdefault('data', {})
        extp = self.get_ext_pillar(hosts)
        for i in [a for a in extp]:
            data[i] = copy.deepcopy(extp[i])
            data[i][TTL_KEY] = self.now
        self.sanitize_and_save(payload, force=True)
        return payload

    def read_cli_args(self):
        """
        Read the command line args passed to the script.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('--ms-debug', action='store_true', default=False)
        parser.add_argument('--list', action='store_true')
        parser.add_argument('--host', action='store')
        parser.add_argument('--all', action='store_true')
        parser.add_argument(
            '--refresh-cache', action='store_true', default=False,
            help=''
            'Force refresh of cache by making API'
            ' requests to cobbler (default: False - use cache files)')
        self.args = parser.parse_args()

    def json_format_dict(self, data, pretty=False):
        """
        Converts a dict to a JSON object and dumps it as a formatted string
        """
        if pretty:
            return json.dumps(data, indent=2)
        else:
            return json.dumps(data)

    def to_stdout(self):
        if self.args.host:
            host = self.hostsvars.get(self.args.hosts, {})
            data_to_print = self.json_format_dict(host, pretty=True)
        else:
            data_to_print = self.json_format_dict(self.inventory, pretty=True)
        print(data_to_print)

MakinaStatesInventory()
# vim:set et sts=4 ts=4 tw=80:
