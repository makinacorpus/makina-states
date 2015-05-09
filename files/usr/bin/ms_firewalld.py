#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import json
import argparse
import six
import logging

import firewall.client
from firewall.client import FirewallClient
from firewall.client import FirewallClientZoneSettings
from firewall.client import FirewallClientServiceSettings

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--config", default='/etc/firewalld.json')
_cache = {}

log = logging.getLogger('makina-states.firewall')


def get_firewall():
    if _cache.get('f') is None:
        _cache['f'] = FirewallClient()
    return _cache['f']


def mark_reload():
    _cache['reload'] = True


def lazy_reload():
    if _cache.get('reload'):
        get_firewall().reload()
        _cache['reload'] = False


def define_zone(z, zdata, masquerade=None):
    if 'target' in zdata:
        msg = 'Configure zone: {0}/{1[target]}'
    else:
        msg = 'Configure zone: {0}'
    log.info(msg.format(z, zdata))
    fw = get_firewall()
    if z not in fw.getZones():
        zn = fw.config().addZone(
            z, FirewallClientZoneSettings())
        zn.setShort(z)
        zn.setDescription(z)
        log.info(' - Zone created')
        mark_reload()
    else:
        zn = fw.config().getZoneByName(z)
    if masquerade is not None:
        cmask = bool(zn.getMasquerade())
        if cmask is not masquerade:
            zn.setMasquerade(masquerade)
            log.info(' - Masquerade: {0}'.format(masquerade))
    target = zdata.get('target', None)
    if target:
        ztarget = "{0}".format(zn.getTarget())
        if target:
            target = {
                'reject': '%%REJECT%%'
            }.get(target.lower(), target.upper())
            if ztarget != target:
                log.info(' - Zone edited')
                zn.setTarget(target)
                mark_reload()


def get_services():
    fw = get_firewall()
    ss = [fw.config().getService(a) for a in fw.config().listServices()]
    services = {}
    for i in ss:
        services[i.get_properties()['name']] = i
    return services


def service_ports(zsettings):
    return [tuple("{0}".format(b) for b in a)
            for a in zsettings.getPorts()]


def define_service(z, zdata):
    if zdata:
        msg = 'configure service: {0} {1}'
    else:
        msg = 'configure service: {0}'
    log.info(msg.format(z, zdata))
    fw = get_firewall()
    aservices = get_services()
    if z not in aservices:
        log.info(' - Service created')
        zsettings = fw.config().addService(
            z, FirewallClientServiceSettings())
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
            log.info(' - Service edited')
            zsettings.setPorts(ports)
            mark_reload()
    zsettings.setShort(z)
    zsettings.setDescription(z)


def configure_rules(z, zdata):
    return


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
    for z, zdata in six.iteritems(jconfig['zones']):
        masq = z in jconfig['public_zones']
        if not masq:
            masq = None
        define_zone(z, zdata, masquerade=masq)
    for z, zdata in six.iteritems(jconfig['services']):
        define_service(z, zdata)
    lazy_reload()
    log.info('end conf')


if __name__ == '__main__':
    main()

# vim:set et sts=4 ts=4 tw=80:
