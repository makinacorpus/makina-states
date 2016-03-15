#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

'''
MakinaStates custom dynamic inventory script for Ansible, in Python.
'''
import re
import subprocess
import argparse
import ConfigParser
import os
import six
from time import time
import logging

re_flags = re.M | re.U | re.S
rei_flags = re.M | re.U | re.S | re.I

try:
    import json
except ImportError:
    import simplejson as json


log = logging.getLogger(__name__)


class MakinaStatesInventory(object):

    def __init__(self):
        self.inventory = {'_meta': {'hostvars': {}}}
        self.debug = False
        self.ms = None
        self.cache_path = None
        self.cache_path_cache = None
        self.cache_max_age = None
        self.read_settings()
        self.read_cli_args()
        self.init_cache()
        self.cache = {}
        self.payload = None
        self.debug = self.args.ms_debug

        update_cache = self.args.refresh_cache
        if not update_cache and not self.is_cache_valid():
            update_cache = True

        if not update_cache:
            if self.debug:
                print('Using {0} cached data, remove the file to use uncached'
                      ' data'.format(self.cache_path_cache))
            self.load_inventory_from_cache()
            # parse cli ARGS and try to see if we miss informations to fullfill
            # hosts that we want to provision and in case, try to refresh the
            # cache

        if update_cache:
            self.update_cache()

        if self.payload:
            if self.payload['data'].keys() == ['local']:
                self.payload['data'] = self.payload['data']['local']
            self.inventory['_meta']['hostvars'].update(self.payload['data'])

        self.make_groups()

        if self.args.host:
            host = self.inventory.get(self.args.hosts, {})
            data_to_print = self.json_format_dict(host, True)
        else:
            data_to_print = self.json_format_dict(self.inventory, True)

        print(data_to_print)

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
        for i in [self.cache_path_cache]:
            if os.path.exists(i):
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
            self.cache_max_age = 24 * 60 * 60
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)
        self.cache_path_cache = self.cache_path + "/ansible-makinastates.cache"

    def load_inventory_from_cache(self):
        """
        Reads the index from the cache file sets self.index
        """
        self.fixperms()
        with open(self.cache_path_cache, 'r') as cache:
            json_inventory = cache.read()
            self.payload = json.loads(json_inventory)

    def write_to_cache(self, data, filename):
        """
        Writes data in JSON format to a file
        """
        json_data = self.json_format_dict(data, True)
        with open(filename, 'w') as cache:
            cache.write(json_data)
            cache.close()
        self.fixperms()

    def json_format_dict(self, data, pretty=False):
        """
        Converts a dict to a JSON object and dumps it as a formatted string
        """
        if pretty:
            return json.dumps(data, indent=2)
        else:
            return json.dumps(data)

    def get_ext_pillar(self):
        process = subprocess.Popen(
            'bin/salt-call --out=json'
            ' mc_remote_pillar.generate_ansible_roster',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.ms)
        stdout, stderr = process.communicate()
        ret = process.wait()
        if ret != 0:
            raise Exception('Something gone wrong with extpillar generation')
        roster = json.loads(stdout)
        return roster

    def update_cache(self):
        """
        Make calls to cobbler and save the output in a cache
        """
        if self.debug:
            print('Computing global salt cache, please wait '
                  'it can take several minutes')
        self.payload = {'time': time(),
                        'data': self.get_ext_pillar()}
        self.write_to_cache(self.payload, self.cache_path_cache)

    def is_cache_valid(self):
        """
        Determines if the cache files have expired, or if it is still valid
        """
        if os.path.isfile(self.cache_path_cache):
            self.load_inventory_from_cache()
        import pdb;pdb.set_trace()  ## Breakpoint ##
        if (
            self.payload and
            (self.payload.get('time', 0) + self.cache_max_age) > time()
        ):
            return True
        return False

    def read_cli_args(self):
        """
        Read the command line args passed to the script.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('--ms-debug', action='store_true', default=False)
        parser.add_argument('--list', action='store_true')
        parser.add_argument('--host', action='store')
        parser.add_argument(
            '--refresh-cache', action='store_true', default=False,
            help=''
            'Force refresh of cache by making API'
            ' requests to cobbler (default: False - use cache files)')
        self.args = parser.parse_args()

    def to_stdout(self):
        print(json.dumps(self.inventory))

MakinaStatesInventory()
# vim:set et sts=4 ts=4 tw=80:
