#!/usr/bin/python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import sys


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
import traceback
import logging
import time

import firewall.client
from firewall.client import FirewallClient
from firewall.client import FirewallClientZoneSettings
from firewall.client import FirewallClientServiceSettings

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--config", default='/etc/firewalld.json')
parser.add_argument("--debug", default=False, action='store_true')
_cache = {}

log = logging.getLogger('makina-states.firewall')
TIMEOUT = 60


def fw():
    '''
    Do no cache calls, and get a client, everytime
    to catch dbus hickups on restart
    '''
    if _cache.get('f') is not None:
        try:
            assert (
                _cache['f'].getRichRules('public') is not None
            )
            time.sleep(0.01)
            assert _cache['f'].getZones() is not None
        except (Exception,):
            cl = _cache.pop('f', None)
            if cl is not None:
                del cl
    if _cache.get('f') is None:
        ttl = time.time() + TIMEOUT
        while (_cache.get('f') is None) and (time.time() < ttl):
            _cache['f'] = FirewallClient()
            if _cache['f'] is not None:
                break
            else:
                time.sleep(0.01)
    if _cache.get('f') is None:
        raise IOError('Cant contact firewalld daemon interface')
    return _cache['f']


def mark_reload():
    _cache['reload'] = True


def lazy_reload():
    if _cache.get('reload'):
        fw().reload()
        _cache['reload'] = False


def get_zones():
    '''
    Early stage wrapper to avoid dbus hicups
    '''
    zones = None
    ttl = time.time() + TIMEOUT
    while (zones is None) and (time.time() < ttl):
        try:
            zones = fw().getZones()
            break
        except (Exception):
            time.sleep(0.01)
    if zones is None:
        raise IOError('Cant get firewall zones')
    return zones


def define_zone(z, zdata, masquerade=None, errors=None):
    if errors is None:
        errors = []
    if 'target' in zdata:
        msg = 'Configure zone {0}: {1[target]}'
    else:
        msg = 'Configure zone {0}'
    log.info(msg.format(z, zdata))
    if z not in get_zones():
        try:
            zn = fw().config().addZone(
                z, FirewallClientZoneSettings())
        except (Exception,) as ex:
            if 'NAME_CONFLICT' in "{0}".format(ex):
                mark_reload()
                lazy_reload()
                if z not in get_zones():
                    zn = fw().config().addZone(
                        z, FirewallClientZoneSettings())
                else:
                    zn = fw().config().getZoneByName(z)
            else:
                raise ex

        zn.setShort(z)
        zn.setDescription(z)
        log.info(' - Zone created')
        mark_reload()
    else:
        zn = fw().config().getZoneByName(z)
    masquerade = bool(masquerade)
    cmask = bool(zn.getMasquerade())
    if cmask is not masquerade:
        zn.setMasquerade(masquerade)
        log.info(' - Masquerade: {0}'.format(masquerade))
    target = zdata.get('target', None)
    if 'target' in zdata:
        ztarget = "{0}".format(zn.getTarget())
        if not target:
            target = 'default'
        if target:
            target = {
                'reject': '%%REJECT%%',
                'default': 'default'
            }.get(target.lower(), target.upper())
        if ztarget != target:
            log.info(' - Zone edited')
            zn.setTarget(target)
            mark_reload()


def get_services(cache=True):
    services = _cache.get('s', {})
    if not services or not cache:
        ss = [fw().config().getService(a)
              for a in fw().config().listServices()]
        services = {}
        for i in ss:
            services[i.get_properties()['name']] = i
        _cache['s'] = services
    return services


def service_ports(zsettings):
    return [tuple("{0}".format(b) for b in a)
            for a in zsettings.getPorts()]


def define_service(z, zdata, errors=None):
    if errors is None:
        errors = []
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
    log.info(msg.format(z, zdata))
    aservices = get_services()
    if z not in aservices:
        aservices = get_services(cache=False)
    if z not in aservices:
        log.info(' - Service created')
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
            log.info(' - Service edited')


def link_interfaces(z, zdata, errors=None):
    if errors is None:
        errors = []
    log.info('Linking interfaces for zone: {0}'.format(z))
    zones = get_zones()
    if z not in zones:
        errors.append({'trace': '',
                       'type': 'interface/nozone',
                       'id': z,
                       'exception': ValueError('no {0}'.format(z))})
    for ifc in zdata.get('interfaces', []):
        try:
            zn = z.lower()
            zone = fw().getZoneOfInterface(ifc)
            if not isinstance(zone, basestring):
                zone = ''
            zone = zone.lower()
            if zone != zn:
                zone = fw().changeZoneOfInterface(z, ifc)
                log.info('Moved {0} to zone {1}'.format(ifc, zone))
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


def configure_rules(z, zdata, errors=None):
    if errors is None:
        errors = []
    log.info('Activating filtering rules for zone: {0}'.format(z))
    for rule in zdata.get('rules', []):
        try:
            # XXX: cache seems dangerous for now
            # inconsistent results :(
            # rules = get_rules(z)
            rules = get_rules(z, cache=False)
            rules_chunks = [sorted(a.split()) for a in rules]
            rule_chunk = sorted(rule.split())
            if rule_chunk not in rules_chunks:
                rules = get_rules(z, cache=False)
                rules_chunks = [sorted(a.split()) for a in rules]
            if rule_chunk not in rules_chunks:
                log.info(' - Add {0}'.format(rule))
                fw().addRichRule(z, rule)
            else:
                log.info(' - Already activated: {0}'.format(rule))
        except (Exception)as ex:
            trace = traceback.format_exc()
            errors.append({'trace': trace,
                           'type': 'rules/rule',
                           'id': "{0}/{1}".format(z, rule),
                           'exception': ex})


def _main(vopts, jconfig, errors=None):
    if errors is None:
        errors = []
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
            define_zone(z, zdata, errors=errors)
        except (Exception,) as ex:
            trace = traceback.format_exc()
            errors.append({'trace': trace,
                           'type': 'zone',
                           'id': z,
                           'exception': ex})
    for z, zdata in six.iteritems(jconfig['services']):
        try:
            define_service(z, zdata, errors=errors)
        except (Exception,) as ex:
            trace = traceback.format_exc()
            errors.append({'trace': trace,
                           'type': 'service',
                           'id': z,
                           'exception': ex})
            log.error(trace)

    for z, zdata in six.iteritems(jconfig['zones']):
        try:
            link_interfaces(z, zdata, errors=errors)
        except (Exception,) as ex:
            trace = traceback.format_exc()
            errors.append({'trace': trace,
                           'type': 'interfaces',
                           'id': z,
                           'exception': ex})

    lazy_reload()

    for z, zdata in six.iteritems(jconfig['zones']):
        try:
            configure_rules(z, zdata, errors=errors)
        except (Exception,) as ex:
            trace = traceback.format_exc()
            errors.append({'trace': trace,
                           'type': 'rules',
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
    elif 'rule/rule' in errortypes:
        code = 4
    elif 'interface' in errortypes:
        code = 5
    elif 'interfaces' in errortypes:
        code = 6
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
    if not os.path.exists(config):
        raise OSError('No config: {0}'.format(config))
        os.exit(1)
    with open(config) as f:
        jconfig = json.loads(f.read())
        if [a for a in jconfig] == ['local']:
            # salt-call cache !?
            jconfig = jconfig['local']
    errors = []
    code = _main(vopts, jconfig, errors=errors)
    old_errors = errors
    errors = []
    if code:
        # on the first run, we can fail the first time
        # specially when switching fw (like with shorewall)
        code = _main(vopts, jconfig, errors=errors)
    old_errors.extend(errors)
    displayed = []
    if errors:
        log.error('ERRORS WHILE CONFIGURATION OF FIREWALL')
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
                except (Exception,) as ex:
                    log.error('EXCEPTION:')
                    log.error(error['exception'])
                if vopts['debug']:
                    try:
                        log.error('TRACE:\n{0}'.format(error['trace']))
                    except (Exception,):
                        log.error('TRACE:')
                        log.error(error['trace'])
            except Exception:
                continue
    return code


if __name__ == '__main__':
    sys.exit(main())

# vim:set et sts=4 ts=4 tw=80:
