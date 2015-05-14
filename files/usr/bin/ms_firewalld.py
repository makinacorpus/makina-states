#!/usr/bin/python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

'''
CONFIGURE FIREWALLD
with a saltstack/makina-states.services.firewall.firewalld:settings
compatible file.
Only the following sections are used::

    - zones
    - services

We use only rich rules to fine grain the restrictions and ease the
managment of rules.

The JSON structure looks like::

.. code-block:: json

   {
     "direct": [
       "ipv4 filter FORWARD 0 -s 2.1.3.2 -j ACCEPT"
     ],
     "zones": {
         "public": {
             "interfaces": [
                 "br0", "eth0", "em0", "br0:0",
             ],
             "rules": [
                 "rule family=\"ipv4\" to service name=\"snmp\" DROP",
                 "rule family=\"ipv4\" to service name=\"dns\" ACCEPT",
                 "rule family=\"ipv4\" to service name=\"http\" ACCEPT",
                 "rule family=\"ipv4\" to service name=\"https\" ACCEPT",
                 "rule family=\"ipv4\" to service name=\"smtp\" ACCEPT",
                 "rule family=\"ipv4\" forward-port port=\"40063\" \
                  protocol=\"tcp\" to-port=\"161\" to-addr=\"10.7.0.25\"",
                 "rule family=\"ipv4\" forward-port port=\"40004\" \
                  protocol=\"udp\" to-port=\"22\" to-addr=\"10.5.0.4\"",
             ],
             "target": "REJECT",
             "services": {
                 "http": {},
                 "https": {},
                 "snmp": {},
                 "smtp": {},
                 "rabbitmq": { "port": [ { "port": "15672" },
                         { "port": "25672" }
                     ] }, "mysql": { "port": [ { "port": "3306" } ] },
                 "mumble": { "port": [ { "port": "64738" } ] },
             },
             "public_services": [ "http", "https", "smtp", "dns", "ssh" ],
             "restricted_services": [ "snmp" ]
         },
      },
      "no_cloud_rules": false,
      "no_default_alias": false,
      "banned_networks": [],
      "aliases": 100,
      "is_container": false,
      "have_rpn": null,
      "internal_zones": ["internal", "dmz", "home", "docker", "lxc", "virt"],
      "public_zones": [ "public", ],
      "default_zone": "public",
      "aliased_interfaces": [ "br0", "eth0", "em0" ],
      "trusted_networks": [],
      "have_docker": true,
      "services": {
          "mongodb": { "port": [ { "port": "27017" } ] },
          "burp": { "port": [ { "port": "4971-4974" } ] },
          "mysql": { "port": [ { "port": "3306" } ] },
          "ssh": {},
          "snmp": {}
      },
      "packages": [ "ipset", "ebtables", "firewalld" ],
      "trust_internal": true,
      "have_vpn": null,
      "permissive_mode": false,
      "enabled": true,
      "have_lxc": false,
      "restricted_services": [ "snmp" ],
      "public_services": [ "http", "https", "smtp", "dns", "ssh" ]
   }


The script:

    - create zones
    - create user defined services
    - activate rich rules onto those rules

Errors are collected but we try not to fail hard and to activate the
maximum of appliable rules.

'''

import os
import json
import argparse
import six
import sys
import copy
import traceback
import logging
import time
import pstats
import cProfile
import datetime

from firewall.functions import splitArgs
from firewall.client import FirewallClient
from firewall.client import FirewallClientZoneSettings
from firewall.client import FirewallClientServiceSettings

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--config", default='/etc/firewalld.json')
parser.add_argument("--debug", default=False, action='store_true')
parser.add_argument("--fromsalt", default=False, action='store_true')
parser.add_argument("--profile", default=False, action='store_true')
_cache = {}

log = logging.getLogger('makina-states.firewall')
TIMEOUT = 20
DEFAULT_TARGET = 'drop'
RUNNINGS = ['RUNNING']


def remove_client():
    if _cache.get('f'):
        client = _cache.pop('f', None)
        if client is not None:
            del client


def fw(retries=6):
    '''
    firewalld interface is nice, but due to DBUS, it is
    a great field for various errors and hickups.

    We then try to get a viable connexion, but also be really
    smart on establishing one
    '''
    # after 2 success full calls to the firewall
    # we assume it is correctly configured
    if _cache.get('f') is not None:
        if _cache.get('f_call', 0) < 2:
            try:
                if _cache['f'].getZones() is None:
                    time.sleep(0.05)
                    assert _cache['f'].getZones() is not None
                _cache.setdefault('f_call', 0)
                _cache['f_call'] += 1
            except (Exception,):
                remove_client()
    if _cache.get('f') is None:
        state = 'notready'
        ttl = time.time() + TIMEOUT
        attempt = 0
        established = False
        loggued = False
        while time.time() < ttl:
            # if we have an instance, we have to wait until the firewall
            # is in the running state
            try:
                attempt += 1
                remove_client()
                _cache['f'] = FirewallClient()
                state = _cache['f'].get_property('state')
                # if we have first contacted the firewall without being
                # in running mode, there is a great chance for the dbus
                # interface to be bugged.
                # So there are two cases,
                # - we assume that the connexion is established only if we
                #   get directly a running state.
                # - In other cases, we assume the firewall to be ready for
                #   commands only on the second successful connection
                #   on the dbus interface.
                if state in RUNNINGS:
                    stop = False
                    if attempt == 1:
                        stop = True
                    elif not established:
                        established = True
                    else:
                        stop = True
                    if stop:
                        log.info('firewalld seems now ready')
                        break
                    continue
                else:
                    established = False
                time.sleep(0.4)
            except (Exception,):
                log.error(traceback.format_exc())
                state = 'unknown'
                # DBUS doent like at all retry spam
                time.sleep(5)
            if not loggued:
                log.error('firewalld is not ready yet,'
                          ' waiting ({0})'.format(state))
                loggued = True
    if _cache.get('f') is None:
        if not retries:
            raise IOError('Cant contact firewalld daemon interface')
        else:
            return fw(retries-1)
    return _cache['f']


def mark_reload():
    _cache['reload'] = True


def lazy_reload():
    if _cache.get('reload'):
        fw().reload()
        _cache['reload'] = False


def get_zones(cache=True):
    '''
    Early stage wrapper to avoid dbus hicups
    '''
    key = 'zones'
    result = _cache.get(key)
    if not result or not cache:
        zones = None
        ttl = time.time() + TIMEOUT
        while (zones is None) and (time.time() < ttl):
            try:
                zones = fw().getZones()
                break
            except (Exception):
                log.error(traceback.format_exc())
                time.sleep(0.01)
        if zones is None:
            raise IOError('Cant get firewall zones')
        result = zones
        _cache[key] = result
    return result


def get_service(s, cache=True):
    key = 'service_{0}'.format(s)
    result = _cache.get(key)
    if not result or not cache:
        result = fw().config().getService(s)
        _cache[key] = result
    return result


def get_services(cache=True):
    key = 'services'
    result = _cache.get(key, {})
    if not result or not cache:
        ss = [get_service(a, cache=cache)
              for a in fw().config().listServices()]
        result = {}
        for i in ss:
            result[i.get_property('name')] = i
        _cache[key] = result
    return _cache[key]


def service_ports(zsettings):
    return [tuple("{0}".format(b) for b in a)
            for a in zsettings.getPorts()]


def in_zones(z):
    zones = get_zones()
    ret = z in zones
    if not ret:
        zones = get_zones(cache=False)
    ret = z in zones
    return ret


def get_zone(z, cache=True):
    k = 'zone_{0}'.format(z)
    result = _cache.get(k, None)
    if not result or not cache:
        result = fw().config().getZoneByName(z)
        _cache[k] = result
    return result


def define_zone(z,
                zdata,
                masquerade=None,
                errors=None,
                changes=None,
                apply_retry=0,
                **kwargs):
    if errors is None:
        errors = []
    if changes is None:
        changes = []
    if 'target' in zdata:
        msg = 'Configure zone {0}: {1[target]}'
    else:
        msg = 'Configure zone {0}'
    log.info(msg.format(z, zdata))
    if not in_zones(z):
        try:
            zn = fw().config().addZone(z, FirewallClientZoneSettings())
        except (Exception,) as ex:
            if 'NAME_CONFLICT' in "{0}".format(ex):
                mark_reload()
                lazy_reload()
                if not in_zones(z):
                    zn = fw().config().addZone(
                        z, FirewallClientZoneSettings())
                else:
                    zn = get_zone(z)
            else:
                raise ex
        zn.setShort(z)
        zn.setDescription(z)
        msg = ' - Zone {0} created'.format(z)
        log.info(msg)
        changes.append(msg)
        mark_reload()
    else:
        zn = get_zone(z)
    masquerade = bool(masquerade)
    cmask = bool(zn.getMasquerade())
    if cmask is not masquerade:
        zn.setMasquerade(masquerade)
        msg = ' - Masquerade: {0}/{1}'.format(z, masquerade)
        log.info(msg)
        changes.append(msg)
    target = zdata.get('target', None)
    if 'target' in zdata:
        ztarget = "{0}".format(zn.getTarget())
        if not target:
            target = DEFAULT_TARGET
        if target:
            target = {
                'reject': '%%REJECT%%',
                'default': 'default'
            }.get(target.lower(), target.upper())
        if ztarget != target:
            msg = ' - Zone {0} edited'.format(z)
            log.info(msg)
            changes.append(msg)
            zn.setTarget(target)
            mark_reload()


def define_service(z,
                   zdata,
                   errors=None,
                   changes=None,
                   apply_retry=0,
                   **kwargs):
    if errors is None:
        errors = []
    if changes is None:
        changes = []
    msg = 'configure service {0}'
    if zdata:
        if zdata.get('port'):
            msg += ':'
        for port in zdata.get('port'):
            portinfo = "{0}".format(port['port'])
            port['protocol'] = 'tcp'
            if 'protocol' in port:
                portinfo = '{0}/{1}'.format(portinfo, port['protocol'])
            if portinfo:
                msg = '{0} {1}'.format(msg, portinfo)
    msg = msg.format(z, zdata)
    log.info(msg)
    aservices = get_services()
    if z not in aservices:
        aservices = get_services(cache=False)
    if z not in aservices:
        msg = ' - Service created {0}'.format(z)
        log.info(msg)
        changes.append(msg)
        zsettings = fw().config().addService(
            z, FirewallClientServiceSettings())
        zsettings.setShort(z)
        zsettings.setDescription(z)
    else:
        zsettings = aservices[z]
    if 'port' in zdata:
        ports = []
        for port in zdata['port']:
            protocols = port.get('protocols', ['udp', 'tcp'])
            for p in protocols:
                pp = (str(port['port']), p)
                if pp not in ports:
                    ports.append(pp)
        diff = False
        sports = service_ports(zsettings)
        if len(sports) != len(ports):
            diff = True
        if not diff:
            for p in ports:
                if p not in sports:
                    diff = True
        if diff:
            zsettings.setPorts(ports)
            mark_reload()
            msg = ' - Service edited {0}'.format(z)
            log.info(msg)
            changes.append(msg)


def link_interfaces(z,
                    zdata,
                    interfaces,
                    errors=None,
                    changes=None,
                    apply_retry=0,
                    **kwargs):
    if errors is None:
        errors = []
    if changes is None:
        changes = []
    msg = 'Linking interfaces for zone: {0}'.format(z)
    log.info(msg)
    if not in_zones(z):
        errors.append({'trace': '',
                       'type': 'interface/nozone',
                       'id': z,
                       'exception': ValueError('no {0}'.format(z))})
    for ifc in zdata.get('interfaces', []):
        if z in interfaces.get(ifc, []):
            msg = '  - {0} already in zone {1}'.format(ifc, z)
            log.info(msg)
            continue
        try:
            zn = z.lower()
            zone = fw().getZoneOfInterface(ifc)
            if not isinstance(zone, basestring):
                zone = ''
            zone = zone.lower()
            if zone != zn:
                zone = fw().changeZoneOfInterface(z, ifc)
                msg = 'Moved {0} to zone {1}'.format(ifc, zone)
                log.info(msg)
                changes.append(msg)
        except (Exception,) as ex:
            trace = traceback.format_exc()
            errors.append({'trace': trace,
                           'type': 'interface',
                           'id': "{0}/{1}".format(z, ifc),
                           'exception': ex})


def get_rules(z, cache=True):
    k = 'rules_{0}'.format(z)
    rules = _cache.get(k, [])
    if not rules or not cache:
        rules = fw().getRichRules(z)
        _cache[k] = rules
    return rules


def get_directs(cache=True):
    k = 'direct_rules'
    rules = _cache.get(k, [])
    if not rules or not cache:
        rules = fw().getAllRules()
        _cache[k] = rules
    return rules


def configure_rules(z,
                    zdata,
                    errors=None,
                    changes=None,
                    apply_retry=0,
                    **kwargs):
    if errors is None:
        errors = []
    if changes is None:
        changes = []
    msg = 'Activating filtering rules for zone: {0}'.format(z)
    log.info(msg)
    for rule in zdata.get('rules', []):
        try:
            # cache can be a source of errors, if we are retrying we
            # skip cache
            if apply_retry > 0:
                rules = get_rules(z, cache=False)
            else:
                rules = get_rules(z)
            rules_chunks = [sorted(a.split()) for a in rules]
            rule_chunk = sorted(rule.split())
            if rule_chunk not in rules_chunks:
                rules = get_rules(z, cache=False)
                rules_chunks = [sorted(a.split()) for a in rules]
            if rule_chunk not in rules_chunks:
                msg = ' - Add {0}/{1}'.format(z, rule)
                log.info(msg)
                changes.append(msg)
                fw().addRichRule(z, rule)
            else:
                msg = ' - Already activated: {0}/{1}'.format(z, rule)
                log.info(msg)
        except (Exception)as ex:
            trace = traceback.format_exc()
            errors.append({'trace': trace,
                           'type': 'rules/rule',
                           'id': "{0}/{1}".format(z, rule),
                           'exception': ex})


def get_direct_chunks(rules):
    rules_chunks = []
    for a in rules[:]:
        chunk = []
        for rulepart in copy.deepcopy(a):
            parts = rulepart
            if not isinstance(parts, (list, tuple, dict, set)):
                parts = [a for a in "{0}".format(parts).split()]
            chunk.extend(sorted([a for a in parts]))
        rules_chunks.append(chunk)
    return rules_chunks


def configure_directs(jconfig,
                      errors=None,
                      changes=None,
                      apply_retry=0,
                      **kwargs):
    if errors is None:
        errors = []
    if changes is None:
        changes = []
    msg = 'Activating direct rules'
    log.info(msg)
    for rule in jconfig.get('direct', []):
        try:
            drule = rule.split(None, 4)
            if len(drule) != 5:
                raise ValueError(
                    '{0} is not formatted as a direct rule'.format(rule))
            rule_chunk = get_direct_chunks([drule])[0]
            # cache can be a source of errors, if we are retrying we
            # skip cache
            if apply_retry > 0:
                rules = get_directs(cache=False)
            else:
                rules = get_directs()
            rules_chunks = get_direct_chunks(rules)
            if rule_chunk not in rules_chunks:
                rules = get_directs()
                rules_chunks = get_direct_chunks(rules)
            if rule_chunk not in rules_chunks:
                msg = ' - Add direct rule {0}'.format(rule)
                log.info(msg)
                changes.append(msg)
                fw().addRule(drule[0],
                             drule[1],
                             drule[2],
                             int(drule[3]),
                             splitArgs(drule[4]))
            else:
                msg = ' - Already activated: {0}'.format(rule)
                log.info(msg)
        except (Exception) as ex:
            trace = traceback.format_exc()
            errors.append({'trace': trace,
                           'type': 'directs/rule',
                           'id': "directs/rule/{0}".format(rule),
                           'exception': ex})


def _main(vopts,
          jconfig,
          errors=None,
          changes=None,
          apply_retry=0,
          **kwargs):
    if errors is None:
        errors = []
    if changes is None:
        changes = []
    # be sure that the firewall client is avalaible and ready
    fw()
    for z, zdata in six.iteritems(jconfig['zones']):
        try:
            masq = z in jconfig['public_zones']
            if not masq:
                masq = None
            # NEVER ACTIVATE GLOBAL MASQUERADE OR WE LL FIND YOU
            # AND WE WILL CUT YOUR FINGERS.
            # define_zone(z, zdata, masquerade=masq, errors=errors)
            # instead, use a rich rule to set masquerade via source/dest
            # matching to restrict correctly the application of the masquerade
            # perimeter
            define_zone(z, zdata, errors=errors, changes=changes,
                        apply_retry=apply_retry, **kwargs)
        except (Exception,) as ex:
            trace = traceback.format_exc()
            errors.append({'trace': trace,
                           'type': 'zone',
                           'id': z,
                           'exception': ex})
    for z, zdata in six.iteritems(jconfig['services']):
        try:
            define_service(z, zdata, errors=errors, changes=changes,
                           apply_retry=apply_retry, **kwargs)
        except (Exception,) as ex:
            trace = traceback.format_exc()
            errors.append({'trace': trace,
                           'type': 'service',
                           'id': z,
                           'exception': ex})
            log.error(trace)

    # for each of our known zones; collect interface mappings
    # this is an optimization as calling getZoneOfInterface is really slow
    interfaces = {}
    try:
        for z, izdata in six.iteritems(jconfig.get('zones', {})):
            for ifc in fw().getInterfaces(z):
                zns = interfaces.setdefault(ifc, [])
                zns.append(z)
    except (Exception,) as ex:
        trace = traceback.format_exc()
        log.error('zone may not exists yet')
        log.error(trace)

    for z, zdata in six.iteritems(jconfig['zones']):
        try:
            link_interfaces(z, zdata, interfaces, errors=errors,
                            changes=changes, apply_retry=apply_retry,
                            **kwargs)
        except (Exception,) as ex:
            trace = traceback.format_exc()
            errors.append({'trace': trace,
                           'type': 'interfaces',
                           'id': z,
                           'exception': ex})

    lazy_reload()

    for z, zdata in six.iteritems(jconfig['zones']):
        try:
            configure_rules(z, zdata, errors=errors, changes=changes,
                            apply_retry=apply_retry, **kwargs)
        except (Exception,) as ex:
            trace = traceback.format_exc()
            errors.append({'trace': trace,
                           'type': 'rules',
                           'id': z,
                           'exception': ex})

    try:
        configure_directs(jconfig, errors=errors, changes=changes,
                          apply_retry=apply_retry, **kwargs)
    except (Exception,) as ex:
        trace = traceback.format_exc()
        errors.append({'trace': trace,
                       'type': 'directs',
                       'id': z,
                       'exception': ex})

    log.info('end conf')
    errortypes = [a['type'] for a in errors]
    if 'zone' in errortypes:
        code = 1
    elif 'service' in errortypes:
        code = 2
    elif 'rules' in errortypes:
        code = 3
    elif 'rules/rule' in errortypes:
        code = 4
    elif 'interface' in errortypes:
        code = 5
    elif 'interfaces' in errortypes:
        code = 6
    elif 'direct/rule' in errortypes:
        code = 7
    elif 'directs' in errortypes:
        code = 8
    elif len(errors):
        code = 255
    else:
        code = 0
    return code


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)-15s %(name)-5s %(levelname)-6s %(message)s')
    log.info('start conf')
    opts = parser.parse_args()
    vopts = vars(opts)
    config = vopts['config']
    if vopts.get('fromsalt'):
        root_logger = logging.getLogger()
        root_logger.disabled = True
    if vopts.get('profile'):
        pr = cProfile.Profile()
        pr.enable()
    if not os.path.exists(config):
        raise OSError('No config: {0}'.format(config))
        os.exit(1)
    with open(config) as f:
        jconfig = json.loads(f.read())
        if [a for a in jconfig] == ['local']:
            # salt-call cache !?
            jconfig = jconfig['local']
    changes = []
    errors = []
    apply_retry = 0
    retries = 3
    while retries:
        retries -= 1
        old_errors = errors
        errors = []
        # on the first run, we can fail the first time
        # specially when switching fw (like with shorewall)
        code = _main(vopts, jconfig,
                     changes=changes,
                     errors=errors,
                     apply_retry=apply_retry)
        for i in reversed(old_errors):
            if i not in errors:
                errors.append(i)
        if code:
            apply_retry += 1
        else:
            break
    old_errors.extend(errors)
    displayed = []
    if errors:
        for error in errors:
            if error in displayed:
                continue
            displayed.append(error)
            try:
                msg = 'TYPE: {0}'.format(error['type'])
                if error.get('id'):
                    msg += ' / id: {0}'.format(error['id'])
                log.error(msg)
                try:
                    log.error('EXCEPTION: {0}'.format(error['exception']))
                except (Exception,):
                    pass
                if vopts['debug']:
                    try:
                        log.error('TRACE:\n{0}'.format(error['trace']))
                    except (Exception,):
                        log.error('TRACE:')
                        log.error(error['trace'])
            except Exception:
                continue
        log.error('ERRORS WHILE CONFIGURATION OF FIREWALL')
        log.error('Return code (0 means configured,'
                  ' even if errors): {0}'.format(code))

    if vopts.get('profile'):
        date = datetime.datetime.now().isoformat()
        if not os.path.exists('/tmp/stats'):
            os.makedirs('/tmp/stats')
        ficp = '/tmp/stats/firewalld.{0}.pstats'.format(date)
        fico = '/tmp/stats/firewalld.{0}.dot'.format(date)
        ficn = '/tmp/stats/firewalld.{0}.stats'.format(date)
        if not os.path.exists(ficp):
            pr.dump_stats(ficp)
            with open(ficn, 'w') as fic:
                pstats.Stats(pr, stream=fic).sort_stats('cumulative')
        log.info('call:\npyprof2calltree '
                 '-i "{0}" -o "{1}"'
                 ''.format(ficp, fico))
    if vopts.get('fromsalt', False):
        if changes:
            changes = '\n'.join(
                [a.replace('"', '').replace("'", '') for a in changes])
            ret = {'changed': True,
                   'comment': (
                       'Firewalld reconfigured --\n'
                       '{0}\n'
                       '"').format(changes)}
        else:
            ret = {'changed': False, 'comment': 'Firewalld in place'}
        print(json.dumps(ret))
    return code


if __name__ == '__main__':
    sys.exit(main())

# vim:set et sts=4 ts=4 tw=80:
