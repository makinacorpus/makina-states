#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

'''
MakinaStates custom dynamic inventory script for Ansible, in Python.
'''
import traceback
import sys
import re
import subprocess
import copy
import argparse
import configparser as ConfigParser
import os
import time
import logging
import pprint

unicode = str
basestring = str


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


def chunkify(l, n):
    n = max(1, n)
    return [l[i:i + n] for i in range(0, len(l), n)]


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


def get_container(pid):
    '''
    On a main host context, for a non containerized process
    this return MAIN_HOST

    On a container context, this return MAIN_HOST
    On a hpot context, this return MAIN_HOST


    '''
    context = 'MAIN_HOST'
    cg = '/proc/{0}/cgroup'.format(pid)
    content = ''
    # lxc ?
    if os.path.isfile(cg):
        with open(cg) as fic:
            content = fic.read()
            if 'lxc' in content:
                # 9:blkio:NAME
                context = content.split('\n')[0].split(':')[-1]
    if '/lxc' in context:
        context = context.split('/lxc/', 1)[1]
    if '/' in context and (
        '.service' in context or
        '.slice' in context or
        '.target' in context
    ):
        context = context.split('/')[0]
    if 'docker' in content:
        context = 'docker'
    return context


def is_this_lxc(pid=1):
    container = get_container(pid)
    if container not in ['MAIN_HOST']:
        return True
    envf = '/proc/{0}/environ'.format(pid)
    if os.path.isfile(envf):
        with open(envf) as fic:
            content = fic.read()
            if 'container=lxc' in content:
                return True
            if 'docker' in content:
                return True
            if os.path.exists('/.dockerinit'):
                return True
    return False


def filter_host_pids(pids):
    thishost = get_container(os.getpid())
    res = [pid for pid in pids if get_container(pid) == thishost]
    return res


def memcached_running():
    if filter_host_pids(
        subprocess.check_output('pgrep memcached || /bin/true',
                                shell=True).split()
    ):
        return True
    return False


def restart_memcached():
    if memcached_running():
        try:
            subprocess.check_output(
                "sudo service memcached restart",
                stderr=subprocess.STDOUT,
                shell=True)
        except subprocess.CalledProcessError:
            trace = traceback.format_exc()
            sys.stderr.write(trace)


class MakinaStatesInventory(object):

    def reset_hosts(self):
        self.hosts = self.inventory['all']['hosts'] = []
        return self.hosts

    def __init__(self):
        self.inventory = {'all': {'hosts': []},
                          '_meta': {'hostvars': {}}}
        self.reset_hosts()
        self.hostvars = self.inventory['_meta']['hostvars']
        self.debug = False
        self.ms = None
        self.groups = {}
        self.cache_path = None
        self.caches = {'list': None, 'hosts': None}
        self.cache_max_age = None
        self.list_cache_age = None
        self.now = time.time()

        self.read_settings()
        self.read_cli_args()
        self.init_cache()
        if os.environ.get('MS_REFRESH_CACHE', ''):
            self.args.refresh_cache = True
        targets = set(
            magic_list_of_strings(os.environ.get('ANSIBLE_TARGETS'))
        )
        targets_groups = set()

        self.refresh_cache = self.args.refresh_cache
        self.debug = self.args.ms_debug

        # in case of cache refreshing, force memcache restart
        if (
            self.args.refresh_cache and
            memcached_running() and
            os.environ.get('NO_MEMCACHE_RESTART', '').lower() not in [
                'y', '1', 1
            ]
        ):
            restart_memcached()

        # we ask first salt for a valid set of hostnames to get pillar from
        # (minionid == fqdn)
        hosts = self.get_list(refresh=self.args.refresh_cache)

        # we get the cache if we have one and we load from there
        # the available hostvars and groups
        payload = self.load_inventory(None, refresh=False)
        self.update_hostvars(targets, targets_groups, hosts, payload)
        self.make_groups()

        # if no targets are selected, we compute the whole infrastructure
        # pillar, and this will be long ! (10min on avg infra)
        full = True
        if targets:
            # but if we detect targets, we check if those are single hosts
            # we will compute pillars only for those hosts
            full = False
            ntargets = set()
            ntargets_groups = set()
            for a in targets:
                if a not in hosts and a not in self.groups:
                    full = True
                    break
                if a in self.groups:
                    ntargets_groups.add(a)
                else:
                    ntargets.add(a)
            # else if we didnt find one, it may be a group, and
            # we compute pillar for all hosts
            if not full:
                targets = ntargets
                targets_groups = ntargets_groups

        if full:
            targets = set([a for a in hosts])
            targets_groups = set()

        for g in targets_groups:
            for h in self.groups.get(g, {}).get('hosts', []):
                targets.add(h)

        # we then load the pillars from each host as the salt_pillar hostvar
        # and salt will also fill ansible connexion hostvars as well
        if targets:
            payload = self.load_inventory(targets, refresh=self.refresh_cache)
            self.update_hostvars(targets, targets_groups, hosts, payload)
            self.make_groups()

        self.filter_targets(targets, targets_groups)
        self.to_stdout()

    def add_group(self, name, hosts=None, groupvars=None):
        if groupvars is None:
            groupvars = {}
        if not hosts:
            hosts = []
        if not isinstance(hosts, (set, list, tuple, dict)):
            hosts = []
        ggroup = self.inventory.setdefault(name, {})
        group = ggroup.setdefault('hosts', [])
        groupvars_ = ggroup.setdefault('vars', {})
        groupvars_.update(groupvars)
        for host in hosts:
            if host not in group:
                group.append(host)
        self.groups[name] = copy.deepcopy(ggroup)

    def pop_group(self, name):
        self.groups.pop(name, None)
        self.inventory.pop(name, None)

    def update_hostvars(self, targets, targets_groups, hosts, payload):
        self.hosts = self.reset_hosts()
        self.hostvars.update(payload['data'])
        for i in hosts + [a for a in self.hostvars]:
            if i not in self.hosts and i in targets:
                self.hosts.append(i)

    def filter_targets(self, targets, targets_groups):
        # filter hosts vars
        for i in [a for a in self.hostvars]:
            found = False
            # if we didnt selected any targets:
            # no filter
            if i in targets:
                found = True
            else:
                for groupn in targets_groups:
                    group = self.groups.get(groupn, [])
                    if group and i in group:
                        found = True
            if not (targets and targets_groups):
                found = True
            if not found:
                self.hostvars.pop(i, None)
        # filter groups vars has no meaning as it is
        # data tied to groups and targets are specified
        # either by CLI or playbook limits
        # if targets_groups:
        #     for i in [a for a in self.groups]:
        #         if i not in targets_groups:
        #             self.pop_group(i)

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
        for g in [a for a in self.groups]:
            self.inventory.pop(g, None)
        for host in [a for a in self.inventory['_meta']['hostvars']]:
            data = self.inventory['_meta']['hostvars'][host]
            try:
                groups = data.get(
                    'salt_pillar', {}).get(
                        'ansible_groups', [])
            except Exception:
                continue
            else:
                # handle the case where groups is just a list
                # of groupnames
                grps = groups
                if not isinstance(groups, dict):
                    grps = {}
                    for a in groups:
                        grps.setdefault(a, {})
                for g in [b for b in grps]:
                    self.add_group(g, hosts=[host], groupvars=grps[g])

    def fixperms(self):
        if os.path.exists(self.cache_path):
            os.chmod(self.cache_path, 0o700)
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
        config = ConfigParser.ConfigParser()
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

    def get_ext_pillar(self, hosts=None, chunksize=16):
        _cmd = ('bin/salt-call --out=json'
                ' mc_remote_pillar.generate_ansible_roster')
        res = {}
        cmds = []
        if hosts:
            if isinstance(hosts, list):
                for chunk in chunkify(hosts, chunksize):
                    cmds.append('{0} {1}'.format(_cmd, ','.join(chunk)))
            else:
                cmds.append('{0} {1}'.format(_cmd, hosts))
        else:
            cmds.append(_cmd)
        for cmd in cmds:
            res.update(self.call_salt(cmd))
        return res

    def sanitize_and_save(self, payload, force=True):
        payload = self.sanitize_payload(payload)
        if payload.setdefault(CACHE_CHANGED_KEY, False) or force:
            self.write_to_cache(payload, self.caches['hosts'])
        return payload

    def load_inventory(self, hosts, refresh=False):
        """
        Reads the index from the cache file sets self.index
        """
        self.fixperms()
        payload = {}
        if os.path.isfile(self.caches['hosts']):
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
            if hosts:
                # In case we have not explicitly asked to not use the cache
                # we only compute pillar for hosts which are not already cached
                if not refresh:
                    hosts = [a
                             for a in hosts
                             if a not in payload['data']]
        if not payload:
            payload = self.sanitize_payload(payload)
        if hosts:
            if refresh:
                # in case of a refresh, purge any cached data
                # that belongs to hosts which we are
                # computing pillar for
                for h in hosts:
                    payload['data'].pop(h, None)
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
            host = self.hostvars.get(self.args.host, {})
            data_to_print = self.json_format_dict(host, pretty=True)
        else:
            data_to_print = self.json_format_dict(self.inventory, pretty=True)
        print(data_to_print)

MakinaStatesInventory()
# vim:set et sts=4 ts=4 tw=80:
