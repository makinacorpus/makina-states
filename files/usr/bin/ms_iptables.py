#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

'''
CONFIGURE a basic iptables based firewall
and takes a configuration file for any further configuration

This firewall is meant to integrate with tools that mess with iptables
by securing a bit (limiting INPUT) and not flushing any already
defined rule if possible
'''

import os
import json
import time
import argparse
import six
import sys
import re
import glob
import copy
import logging
import subprocess
import fcntl


def uniquify(seq):
    '''uniquify a list'''
    seen = set()
    return [x for x in seq
            if x not in seen and not seen.add(x)]


def lock(fd, flags=fcntl.LOCK_NB | fcntl.LOCK_EX):
    fcntl.flock(fd.fileno(), flags)


def unlock(fd):
    fcntl.flock(fd.fileno(), fcntl.LOCK_UN)


DESC = '''
ms_iptables.py [--config=f]
    - set the 'harden rules', by default: INPUT policy is DROP
    - apply the default rules (accept loopback traffic, and
      input dns, ssh, http(s)
ms_iptables.py --clear [--config=f]
    - set all iptables policies to ACCEPT and remove any rule

ms_iptables.py --stop [--config=f]
    - set all iptables policies to ACCEPT and remove any rule
    - remove any defined rule that are configured
    - this must leave the firewall with other tools iptables
      left as-is

ms_iptables.py --open [--config=f]
    - set the firewall policy to OPEN
ms_iptables.py --hard [--config=f]
    - set the firewall policy to hard (prevalent on open mode)

ms_iptables.py --flush [--config=f]
    - same as called without argument, but flush any existing rule
      before applying anything

ms_iptables.py --no-rules [--config=f]
    - Launch firewall with configured policy mode, but do not load rules


NOTES:
    - --config=f => "f" is a configuration file in the JSON format in the form
    - --config-dir=d => "d" is a directory where you can add conf files
      which will be merged to the whole config
    - multiple config files can be given (--config=a --config=b), they
      will be merged
    - Any section not declared will default to the default config defined in
      DEFAULT_FIREWALL variable (see: {fle})
    - Please use 'ip*tables -w' to get a lock and avoid misconfigurations


ms_iptables.py is configurable via a json configuration file

  {{
      'policy': 'hard' / 'open', default firewall policy,
      'open_policies': ['List of iptables commands to flush the fw'],
      'hard_policies': ['List of iptables commands to make the fw harden'],
      'flush_rules: ['List of iptables commands to flush the fw'],
      'rules': ['List of iptables commands to apply tp the firewall']
      'load_default_rules': [true]/false, =>
         if true, the default  rules will be
         appended to any defined rules
      'load_default_flush_rules': [true]/false, =>
         if true, the default flush_rules rules will be
         appended to any defined rules
      'load_default_open_policies': [true]/false, =>
         if true, the default open_policies rules
         will be appended to any defined rules
      'load_default_hard_policies': [true]/false, =>
         if true, the default hard_policies rules
         will be appended to any defined rules
      'no_rules': null / true / false, if true, do not apply control rules
  }}

EG: to add the port 8080 and a log/drop on masquerade/input, plus a custom rule
    /etc/ms_iptables.json:
  {{
      'rules': [
       'ip6tables -w -t filter -I  INPUT 1 -p tcp --dport 8080 -j ACCEPT',
       'iptables  -w -t filter -I  INPUT 1 -p tcp --dport 8080 -j ACCEPT',
       'iptables -w -t filter -A POSTROUTING -s 192.168.122.0/24\
  ! -d 192.168.122.0/24 -j MASQUERADE']
  }}

{fle}
'''.format(fle=__file__)
parser = argparse.ArgumentParser(DESC)
default_configs = []
if os.path.exists('/etc/ms_iptables.json'):
    default_configs.append('/etc/ms_iptables.json')
parser.add_argument("--config", nargs='+', default=default_configs)
parser.add_argument("--config-dir", nargs='+', default=['/etc/ms_iptables.d'])
parser.add_argument("--debug", default=False, action='store_true')
parser.add_argument("--from-salt", default=False, action='store_true')


parser.add_argument(
    "--open",
    help="Open firewall policies to a permissive state",
    default=False, action='store_true')

parser.add_argument(
    "--stop",
    help="Stop the firewall (policies & rules) to a permissive state",
    default=False, action='store_true')

parser.add_argument(
    "--clear",
    help="Flush the firewall (policies & rules) to a permissive state",
    default=False, action='store_true')

parser.add_argument(
    "--flush",
    help="Flush all the firewall rules before applying anything",
    default=False, action='store_true')

parser.add_argument(
    "--no-state",
    help="Do no store state (dangerous)",
    default=False, action='store_true')
parser.add_argument(
    "--state-file",
    help="store/load the firewall state in/from this file",
    default='/run/ms_iptables.state')

parser.add_argument(
    "--lock-file",
    help="store/load the firewall lock in/from this file",
    default='/run/ms_iptables.lock')

parser.add_argument("--no-rules",
                    help="Do not apply rules",
                    default=False, action='store_true')

parser.add_argument(
    "--no-ipv6",
    help="Do not try to apply rules for an IPv6 firewall",
    default=False, action='store_true')

_cache = {}

log = logging.getLogger('makina-states.ms_iptables')
TIMEOUT = 20
re_flags = re.M | re.U | re.I


DEFAULT_FIREWALL = {
    'ipv6': True,
    'load_default_open_policies': True,
    'load_default_hard_policies': True,
    'load_default_flush_rules': True,
    'load_default_rules': True,
    'policy': 'hard',
    'open_policies': [
        'iptables  -w -t filter -P INPUT       ACCEPT',
        'iptables  -w -t filter -P OUTPUT      ACCEPT',
        'iptables  -w -t filter -P FORWARD     ACCEPT',
        'iptables  -w -t mangle -P PREROUTING  ACCEPT',
        'iptables  -w -t mangle -P INPUT       ACCEPT',
        'iptables  -w -t mangle -P FORWARD     ACCEPT',
        'iptables  -w -t mangle -P OUTPUT      ACCEPT',
        'iptables  -w -t mangle -P POSTROUTING ACCEPT',
        'iptables  -w -t nat    -P PREROUTING  ACCEPT',
        'iptables  -w -t nat    -P INPUT       ACCEPT',
        'iptables  -w -t nat    -P OUTPUT      ACCEPT',
        'iptables  -w -t nat    -P POSTROUTING ACCEPT',
        'ip6tables -w -t filter -P INPUT       ACCEPT',
        'ip6tables -w -t filter -P OUTPUT      ACCEPT',
        'ip6tables -w -t filter -P FORWARD     ACCEPT',
        'ip6tables -w -t mangle -P PREROUTING  ACCEPT',
        'ip6tables -w -t mangle -P INPUT       ACCEPT',
        'ip6tables -w -t mangle -P FORWARD     ACCEPT',
        'ip6tables -w -t mangle -P OUTPUT      ACCEPT',
        'ip6tables -w -t mangle -P POSTROUTING ACCEPT',
        'ip6tables -w -t nat    -P PREROUTING  ACCEPT',
        'ip6tables -w -t nat    -P INPUT       ACCEPT',
        'ip6tables -w -t nat    -P OUTPUT      ACCEPT',
        'ip6tables -w -t nat    -P POSTROUTING ACCEPT'
    ],
    'hard_policies': [
        'iptables  -w -t filter -P INPUT       DROP',
        'iptables  -w -t filter -P OUTPUT      ACCEPT',
        'iptables  -w -t filter -P FORWARD     ACCEPT',
        'iptables  -w -t mangle -P PREROUTING  ACCEPT',
        'iptables  -w -t mangle -P INPUT       ACCEPT',
        'iptables  -w -t mangle -P FORWARD     ACCEPT',
        'iptables  -w -t mangle -P OUTPUT      ACCEPT',
        'iptables  -w -t mangle -P POSTROUTING ACCEPT',
        'iptables  -w -t nat    -P PREROUTING  ACCEPT',
        'iptables  -w -t nat    -P INPUT       ACCEPT',
        'iptables  -w -t nat    -P OUTPUT      ACCEPT',
        'iptables  -w -t nat    -P POSTROUTING ACCEPT',
        'ip6tables -w -t filter -P INPUT       DROP',
        'ip6tables -w -t filter -P OUTPUT      ACCEPT',
        'ip6tables -w -t filter -P FORWARD     ACCEPT',
        'ip6tables -w -t mangle -P PREROUTING  ACCEPT',
        'ip6tables -w -t mangle -P INPUT       ACCEPT',
        'ip6tables -w -t mangle -P FORWARD     ACCEPT',
        'ip6tables -w -t mangle -P OUTPUT      ACCEPT',
        'ip6tables -w -t mangle -P POSTROUTING ACCEPT',
        'ip6tables -w -t nat    -P PREROUTING  ACCEPT',
        'ip6tables -w -t nat    -P INPUT       ACCEPT',
        'ip6tables -w -t nat    -P OUTPUT      ACCEPT',
        'ip6tables -w -t nat    -P POSTROUTING ACCEPT'
    ],
    'flush_rules': [
        'iptables -w -t filter -F OUTPUT',
        'iptables -w -t filter -F INPUT',
        'iptables -w -t filter -F FORWARD',
        'iptables -w -t mangle -F PREROUTING',
        'iptables -w -t mangle -F INPUT',
        'iptables -w -t mangle -F FORWARD',
        'iptables -w -t mangle -F OUTPUT',
        'iptables -w -t mangle -F POSTROUTING',
        'iptables -w -t nat    -F PREROUTING',
        'iptables -w -t nat    -F INPUT',
        'iptables -w -t nat    -F OUTPUT',
        'iptables -w -t nat    -F POSTROUTING',
        'ip6tables -w -t filter -F OUTPUT',
        'ip6tables -w -t filter -F INPUT',
        'ip6tables -w -t filter -F FORWARD',
        'ip6tables -w -t mangle -F PREROUTING',
        'ip6tables -w -t mangle -F INPUT',
        'ip6tables -w -t mangle -F FORWARD',
        'ip6tables -w -t mangle -F OUTPUT',
        'ip6tables -w -t mangle -F POSTROUTING',
        'ip6tables -w -t nat    -F PREROUTING',
        'ip6tables -w -t nat    -F INPUT',
        'ip6tables -w -t nat    -F OUTPUT',
        'ip6tables -w -t nat    -F POSTROUTING'
    ],
    'rules': [
        'iptables -w -t filter -I  INPUT 1'
        ' -m state --state RELATED,ESTABLISHED -j ACCEPT',
        'iptables -w -t filter -I OUTPUT 1 -o lo -j ACCEPT',
        'iptables -w -t filter -I  INPUT 1 -i lo -j ACCEPT',
        'iptables -w -t filter -I  INPUT 1 -p icmp -j ACCEPT',
        'iptables -w -t filter -I  INPUT 1 -p tcp --dport 22  -j ACCEPT',
        'iptables -w -t filter -I  INPUT 1 -p udp --dport 22  -j ACCEPT',
        'iptables -w -t filter -I  INPUT 1 -p tcp --dport 80  -j ACCEPT',
        'iptables -w -t filter -I  INPUT 1 -p tcp --dport 443 -j ACCEPT',
        'iptables -w -t filter -I  INPUT 1 -p tcp --dport 25  -j ACCEPT',
        'iptables -w -t filter -I  INPUT 1 -p tcp --dport 53  -j ACCEPT',
        'iptables -w -t filter -I  INPUT 1 -p udp --dport 53  -j ACCEPT',
        'ip6tables -w -t filter -I  INPUT 1'
        ' -m state --state RELATED,ESTABLISHED -j ACCEPT',
        'ip6tables -w -t filter -I OUTPUT 1 -o lo -j ACCEPT',
        'ip6tables -w -t filter -I  INPUT 1 -i lo -j ACCEPT',
        'ip6tables -w -t filter -I  INPUT 1 -p icmp -j ACCEPT',
        'ip6tables -w -t filter -I  INPUT 1 -p icmpv6 -j ACCEPT',
        'ip6tables -w -t filter -I  INPUT 1 -p tcp --dport 22  -j ACCEPT',
        'ip6tables -w -t filter -I  INPUT 1 -p tcp --dport 80  -j ACCEPT',
        'ip6tables -w -t filter -I  INPUT 1 -p tcp --dport 443 -j ACCEPT',
        'ip6tables -w -t filter -I  INPUT 1 -p tcp --dport 25  -j ACCEPT',
        'ip6tables -w -t filter -I  INPUT 1 -p tcp --dport 53  -j ACCEPT',
        'ip6tables -w -t filter -I  INPUT 1 -p udp --dport 53  -j ACCEPT'
    ]
}
MODES = ['policy']
RULES_AND_POLICIES = ['rules', 'flush_rules',
                      'hard_policies', 'open_policies']
FLAGS = ['ipv6', 'load_default_open_policies', 'load_default_rules',
         'load_default_hard_policies', 'load_default_flush_rules']
appliedrule_re = re.compile(
    '(?P<binary>ip6?tables)\s+'
    '(-w\s+)?'
    '(-t\s+(?P<table>(filter|nat|mangle))\s+)?'
    '(?P<action>-I|-A)\s+'
    '(?P<chain>OUTPUT|INPUT|FORWARD|POSTROUTING|PREROUTING)\s+'
    '((?P<index>[0-9]+)\s+)?'
    '(?P<rule>.*$)',
    flags=re_flags)
policyrule_re = re.compile(
    '(?P<binary>ip6?tables)\s+'
    '(-w\s+)?'
    '(-t\s+(?P<table>(filter|nat|mangle))\s+)?'
    '(?P<switch>-P)\s+'
    '(?P<chain>OUTPUT|INPUT|FORWARD|POSTROUTING|PREROUTING)\s+'
    '(?P<policy>ACCEPT|REJECT|DROP)',
    flags=re_flags)
policyout_re = re.compile(' (?P<policy>ACCEPT|DROP|REJECT)\)')


class InvalidConfiguration(ValueError):
    pass


def popen(cmd, **kwargs):
    kw = {'shell': True}
    kw.update(kwargs)
    return subprocess.Popen(cmd, **kw)


def load_config(fcfg, merged_config=None):
    with open(fcfg) as fic:
        config = json.loads(fic.read())
        if not isinstance(config, dict):
            raise ValueError('not a valid dict json format')
    error_msgs = []
    for section in RULES_AND_POLICIES:
        if not isinstance(config.get(section, []), list):
            error_msgs.append('{0} is not a list'.format(section))
    for section in FLAGS:
        if not isinstance(config.get(section, True), bool):
            error_msgs.append('{0} is not a boolean'.format(section))
    for section in MODES:
        if not isinstance(config.get('section', ''), six.string_types):
            error_msgs.append('{0} is not a string'.format(section))
    if error_msgs:
        raise InvalidConfiguration(
            'config file is invalid:\n * {0}'.format(
                ' * '.join(error_msgs)))
    if merged_config:
        for section, val in six.iteritems(merged_config):
            if section in FLAGS and section not in config:
                config[section] = val
            config.setdefault(section, [])
            if section in RULES_AND_POLICIES:
                config[section].extend(val[:])
    return config


def validate_and_complete(vopts, config):
    for section in FLAGS + MODES + RULES_AND_POLICIES:
        use_default = True
        loadk = 'load_default_{0}'.format(section)
        if (
            (section in RULES_AND_POLICIES) and
            not config.setdefault(loadk,
                                  copy.deepcopy(DEFAULT_FIREWALL[loadk]))
        ):
            use_default = False
        if use_default:
            config.setdefault(section,
                              copy.deepcopy(DEFAULT_FIREWALL[section]))
            if section in RULES_AND_POLICIES:
                for val in DEFAULT_FIREWALL[section]:
                    if val not in config[section]:
                        config[section].append(val)
        if (
            (vopts['clear'] or vopts['stop']) and
            (section in RULES_AND_POLICIES)
        ):
            config[section] = uniquify(config[section])
        if section == 'policy' and config['policy'] not in ['open', 'hard']:
            config['policy'] = DEFAULT_FIREWALL['policy']
        if vopts['open'] or vopts['clear'] or vopts['stop']:
            config['policy'] = 'open'
    if vopts['no_ipv6']:
        config['ipv6'] = False
    return config


def load_configs(vopts, config=None, use_cache=True):
    if (
        use_cache and
        os.path.exists(vopts['state_file']) and
        vopts['state_file'] not in vopts['config']

    ):
        vopts['config'].insert(0, vopts['state_file'])
    for fcfgdir in vopts['config_dir']:
        if os.path.exists(fcfgdir):
            for cfg in sorted(glob.glob('{0}/*.json'.format(fcfgdir))):
                if cfg not in vopts['config']:
                    vopts['config'].append(cfg)
    invalid_cfgs = []
    for fcfg in vopts['config']:
        try:
            config = load_config(fcfg, merged_config=config)
        except (OSError, IOError, ValueError) as exc:
            invalid_cfgs.append(fcfg)
            log.error('{0} is not valid'.format(fcfg))
            log.error('{0}'.format(exc))
    # we fail the firewall completly only in the case of apply
    # in case of a stop or a clear, we try to best effort
    # even relying on a default FW
    if invalid_cfgs and not(vopts['stop'] or vopts['clear']):
        raise InvalidConfiguration(
            'Firewall will not load, configuration is invalid')
    else:
        # invalid configuration files may result in an empty config
        if not config:
            config = copy.deepcopy(DEFAULT_FIREWALL)
    validate_and_complete(vopts, config)
    return config


def apply_rule(raw_rule, config):
    rule = raw_rule
    if '{' in config and '}' in config:
        rule = rule.format(**config)
    to_apply = True
    ret = None
    if 'ip6tables' in rule and not config.get('ipv6', True):
        log.info('{0} won\'t be applied, '
                 'ipv6 support is disabled'.format(rule))
        to_apply = False
    if not to_apply:
        return ret
    pobj = policyrule_re.search(rule)
    if pobj:
        pgroups = pobj.groupdict()
        table = pgroups['table']
        chain = pgroups['chain']
        binary = pgroups['binary']
        if not table:
            table = 'filter'
        pout = popen(
            '{binary} -t {table} -L {chain} | head -n1'
            ''.format(chain=chain, table=table, binary=binary),
            stdout=subprocess.PIPE)
        pret = pout.wait()
        if pret:
            policy = None
        else:
            out = pout.stdout.read().strip()
            policy = policyout_re.search(out)
            if policy:
                policy = policy.groupdict()['policy']
        if policy == pgroups['policy']:
            to_apply = False
            log.info('{0} policy already applied'.format(rule))
    elif appliedrule_re.search(rule):
        crule = appliedrule_re.sub('\g<binary> -C  \g<chain> \g<rule>', rule)
        p = popen(crule, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cret = p.wait()
        if cret:
            to_apply = True
        else:
            to_apply = False
            log.info('{0} already applied'.format(rule))
    if to_apply:
        log.info('{0} applied'.format(rule))
        p = popen(rule)
        ret = p.wait()
        if ret:
            log.error('{0} failed'.format(rule))
    return ret


def remove_rule(raw_rule, config):
    rule = raw_rule
    if '{' in config and '}' in config:
        rule = rule.format(**config)
    to_apply = True
    ret = None
    if 'ip6tables' in rule and not config.get('ipv6', True):
        log.info('{0} won\'t be applied, '
                 'ipv6 support is disabled'.format(rule))
        to_apply = False
    if not to_apply:
        return ret
    pobj = policyrule_re.search(rule)
    robj = appliedrule_re.search(rule)
    drule = None
    if pobj:
        pgroups = pobj.groupdict()
        table = pgroups['table']
        chain = pgroups['chain']
        binary = pgroups['binary']
        if not table:
            table = 'filter'
        pout = popen(
            '{binary} -t {table} -L {chain} |head -n1'
            ''.format(chain=chain, table=table, binary=binary),
            stdout=subprocess.PIPE)
        pret = pout.wait()
        if pret:
            policy = None
        else:
            out = pout.stdout.read().strip()
            policy = policyout_re.search(out)
            policy = policy.groupdict()['policy']
        if policy == 'ACCEPT':
            to_apply = False
            log.info('{0} policy already cleared'.format(rule))
        else:
            rule = rule.replace('DROP', 'ACCEPT')
            rule = rule.replace('REJECT', 'ACCEPT')
    elif robj:
        pgroups = robj.groupdict()
        if not pgroups['table']:
            pgroups['table'] = 'filter'
        crule = '{binary} -t {table} -C {chain} {rule}'.format(**pgroups)
        p = popen(crule, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cret = p.wait()
        if cret:
            to_apply = False
            log.info('{0} already removed'.format(rule))
        else:
            to_apply = True
            drule = ('{binary} -w -t {table} -D {chain} {rule}'
                     '').format(**pgroups)
    if to_apply:
        if drule:
            rule = drule
        log.info('{0} applied'.format(rule))
        p = popen(rule)
        ret = p.wait()
        # try to remove extra rules if we leaked two times
        # and inserted the same rule a bunch of times
        tries = 10000
        while tries > 0:
            tries -= 1
            p = popen(rule, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            iret = p.wait()
            if iret:
                break
        if ret:
            log.error('{0} failed'.format(rule))
    return ret


def report(rule, ret, errors=None, changes=None):
    if errors is None:
        errors = []
    if changes is None:
        changes = []
    if ret is not None:
        if ret == 0:
            changes.append(rule)
        else:
            errors.append(rule)
    return errors, changes


def flush_fw(config, errors=None, changes=None):
    if errors is None:
        errors = []
    if changes is None:
        changes = []
    log.info('Flushing the firewall')
    for r in config['flush_rules']:
        report(r, apply_rule(r, config), errors, changes)
    return errors, changes


def apply_policies(config, errors=None, changes=None):
    if errors is None:
        errors = []
    if changes is None:
        changes = []
    log.info('Configuring the firewall policies'
             ' (mode: {policy})'.format(**config))
    for r in config['{policy}_policies'.format(**config)]:
        report(r, apply_rule(r, config), errors, changes)
    return errors, changes


def remove_rules(config, errors=None, changes=None):
    if errors is None:
        errors = []
    if changes is None:
        changes = []
    log.info('Removing rules from firewall')
    for r in config['rules']:
        report(r, remove_rule(r, config), errors, changes)
    return errors, changes


def apply_rules(config, errors=None, changes=None):
    if errors is None:
        errors = []
    if changes is None:
        changes = []
    log.info('Applying rules to firewall')
    for r in config['rules']:
        report(r, apply_rule(r, config), errors, changes)
    return errors, changes


def cleanup_old_rules(cache_config, config, errors=None, changes=None):
    log.info('Cleaning up the firewall from obsolete rules')
    if errors is None:
        errors = []
    if changes is None:
        changes = []
    for rule in cache_config['rules']:
        if rule not in config['rules']:
            report(rule, remove_rule(rule, config), errors, changes)
    return errors, changes


def _main(timeout=60):
    opts = parser.parse_args()
    code = 0
    vopts = vars(opts)
    if vopts['debug']:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)-15s %(name)-5s %(levelname)-6s %(message)s')
    log.info('Firewall: start configuration')
    ret = {'changed': False, 'comment': 'Firewall in place', 'result': None}
    errors, changes = [], []
    try:
        config = load_configs(vopts, use_cache=False)
        cache_config = load_configs(vopts, use_cache=True)
    except (InvalidConfiguration,) as exc:
        errors.append('{0}'.format(exc))
    else:
        now = time.time()
        end = now + timeout
        lockp = vopts['lock_file']
        if not os.path.exists(lockp):
            with open(lockp, 'w') as fic:
                fic.write('')
        locko = open(lockp)
        has_lock = False
        while time.time() < end:
            try:
                lock(locko)
                has_lock = True
                break
            except IOError:
                log.error('Locked: wait')
                time.sleep(0.5)
        if has_lock:
            if not vopts['stop'] and (vopts['clear'] or vopts['flush']):
                flush_fw(config, errors, changes)
            cleanup_old_rules(cache_config, config, errors=errors, changes=changes)
            if not vopts['no_state']:
                with open(vopts['state_file'], 'w') as fic:
                    fic.write(
                        json.dumps(config, indent=2, separators=(',', ': ')))
            if not (vopts['clear'] or vopts['no_rules']):
                if vopts['stop']:
                    remove_rules(config, errors, changes)
                else:
                    apply_rules(config, errors, changes)
            apply_policies(config, errors, changes)
            unlock(locko)
        else:
            errors.append('Another instance is locking the firewall')
    if errors:
        ret['result'] = False
        code = 1
        ret['comment'] = 'Firewall failed configuration'
        for e in errors:
            ret['comment'] += '\n * {0}'.format(e)
    elif changes:
        ret['result'] = True
        if vopts['stop']:
            ret['comment'] = 'Firewall cleared'
    log.info(ret['comment'])
    if vopts['from_salt']:
        print(json.dumps(ret))
    return code, ret


def main():
    sys.exit(_main()[0])


if __name__ == '__main__':
    sys.exit(main())
# vim:set et sts=4 ts=4 tw=80:
