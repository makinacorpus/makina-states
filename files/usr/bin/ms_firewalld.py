#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import json
import argparse
import six

import firewall.client
from firewall.client import FirewallClient
from firewall.client import FirewallClientZoneSettings

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--config", default='/etc/firewalld.json')
_cache = {}


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


def define_zone(z, zdata):
    fw = get_firewall()
    if z not in fw.getZones():
        zsettings = fw.config().addZone(
            z, FirewallClientZoneSettings())
        zsettings.setShort(z)
        zsettings.setDescription(z)
        mark_reload()


def edit_zone(z, zdata):
    edit = False
    target = zdata.get('target', None)
    if target:
        edit = True
    if edit:
        fw = get_firewall()
        cfg = fw.config()
        zn = cfg.getZoneByName(z)
        ztarget = "{0}".format(zn.getTarget())
        if target and ztarget != target:
            zn.setTarget(ztarget)
            mark_reload()


def main():
    opts = parser.parse_args()
    vopts = vars(opts)
    config = vopts['config']
    if not os.path.exists(config):
        raise OSError('No config: {0}'.format(config))
        os.exit(1)
    with open(config) as f:
        jconfig = json.loads(f.read())
    for z, zdata in six.iteritems(jconfig['zones']):
        define_zone(z, zdata)
        edit_zone(z, zdata)
    lazy_reload()


if __name__ == '__main__':
    main()

# vim:set et sts=4 ts=4 tw=80:
