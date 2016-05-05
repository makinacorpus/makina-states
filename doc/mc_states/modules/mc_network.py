#!/usr/bin/network python
# -*- coding: utf-8 -*-
'''

.. _module_mc_network:

mc_network / network registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_network

'''
import yaml
import requests
import ipaddr
# Import python libs
import os
import logging
import time
from pprint import pformat
import copy
import mc_states.api
import datetime
import re
from salt.utils.odict import OrderedDict
import traceback

try:
    import whois
    HAS_PYWHOIS = True
except ImportError:
    HAS_PYWHOIS = False
try:
    from ipwhois import IPWhois
    HAS_IPWHOIS = True
except ImportError:
    HAS_IPWHOIS = False

from mc_states.api import six
from mc_states.api import is_valid_ip
import contextlib
import socket
import urllib2

# Import salt libs
from salt.utils.validate.net import ipv4_addr as _ipv4_addr

__name = 'network'

log = logging.getLogger(__name__)


def mainip():
    return __salt__['cmd.run']("ip route get 1 | awk '{print $NF;exit}'",
                               python_shell=True)

def hostname():
    return socket.getfqdn()


def default_net():
    '''
    Function to be used on a running system (opposed to settings)
    Use by default a bridge (with main interface as the only first port)
    or the main interface as the link with internet
    '''
    gifaces = __grains__['ip_interfaces'].items()
    default_route = __grains__.get('makina.default_route', OrderedDict())
    # default mode: masquerading on the interface containing
    # the default route for lxc and docker containers
    # later, we will add maybe support for failover ip bridges/ vmac
    nifaces = [a[0] for a in gifaces
               if 'veth' not in a and
               'br' not in a and
               'tun' not in a and
               'tap' not in a]
    brifs = [a for a in nifaces if 'br' in a]
    if 'eth0' in nifaces:
        default_if = 'eth0'
    else:
        default_if = nifaces[0]
    # if a bridge has the if port, use that instead
    v4addr = [a
              for a in __grains__['ip_interfaces'].get(default_if, [])
              if ':' not in a]
    if brifs and not v4addr:
        for br in brifs:
            res = __salt__['cmd.run'](
                'brctl show {0}'.format(br), python_shell=True)
            ifs = []
            for line in res.split('\n'):
                ifs.append(line.split()[-1].replace('\n', ''))
            if default_if in ifs:
                default_if = br
                break
    try:
        default_net_ = '.'.join(
            [a for a in gifaces
             if a[0] == default_if][
                 0][1][0].split('.')[:3] + ['0'])
        parts = default_net_.split('.')
        parts.reverse()
        default_netmask = 32
        for part in parts:
            if part == '0':
                default_netmask -= 8
            else:
                break
    except Exception:
        default_net_ = None
        default_netmask = 32
    return {'default_route': default_route,
            'default_net': default_net_,
            'default_netmask': default_netmask,
            'gifaces': gifaces,
            'nifaces': nifaces,
            'brifs': brifs,
            'default_if': default_if}


def sort_ifaces(infos):
    a = infos[0]
    key = a
    if re.match('^(eth0)', key):
        key = '100___' + a
    if re.match('^(eth[123456789][0123456789]+\|em|wlan)', key):
        key = '200___' + a
    if re.match('^(lxc\|docker)', key):
        key = '300___' + a
    if re.match('^(veth\|lo)', key):
        key = '900___' + a
    return key


def get_broadcast(dn, ip):
    '''Get a server broadcase
    ipsubnet.255
    '''
    num = '255'
    gw = '.'.join(ip.split('.')[:-1] + [num])
    return gw


def get_netmask(dn, ip):
    '''Get a server netmask
    default to ipsubnet.255
    '''
    netmask = '255.255.255.0'
    return netmask


def get_gateway(dn, ip):
    '''Get a server gateway
    default to ipsubnet.254
    except for online where the gw == ipsubnet.1
    '''
    num = '254'
    if 'online-' in dn:
        num = '1'
    gw = '.'.join(ip.split('.')[:-1] + [num])
    return gw


def get_dnss(dn, ip):
    '''Get server dnss
    '''
    defaults = ['127.0.0.1', '8.8.8.8', '4.4.4.4']
    if 'sys-' in dn:
        defaults.insert(1, '213.186.33.99')
    if 'ovh-' in dn:
        defaults.insert(1, '213.186.33.99')
    if 'online-' in dn:
        defaults.insert(1, '62.210.16.6')
        defaults.insert(1, '62.210.16.7')
    return ' '.join(defaults)


def get_fo_netmask(dn, ip):
    '''Get netmask for an ip failover
    '''
    netmask = '255.255.255.255'
    return netmask


def get_fo_broadcast(dn, ip):
    '''Get broadcast for an ip failover
    '''
    broadcast = ip
    return broadcast


def settings():
    '''
    network registry

    networkManaged
        Do we manage the network configuration
    interfaces
        Dict of configuration for network interfaces
    main_ip
      main server ip
    hostname
      main hostname
    domain
      main domain
    devhost_ip
      devhost ip
    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        _s = __salt__
        grains = __grains__
        pillar = __pillar__
        data = {'interfaces': {}, 'ointerfaces': []}
        grainsPref = 'makina-states.localsettings.'
        providers_ = __salt__['mc_provider.settings']()
        # Does the network base config file have to be managed via that
        # See makina-states.localsettings.network
        # Compat for the first test!
        data['networkManaged'] = (
            _s['mc_utils.get']('makina-states.network_managed', False) or
            _s['mc_utils.get'](grainsPref + 'network.managed', False))
        # ip managment
        default_ip = None
        ifaces = grains['ip_interfaces'].items()
        ifaces.sort(key=sort_ifaces)
        devhost_ip = None
        forced_ifs = {}
        devhost = __salt__['mc_nodetypes.is_devhost']()
        real_ifaces = [(a, ip)
                       for a, ip in ifaces
                       if 'br' not in a and
                       'docker' not in a and
                       'tun' not in a and
                       not a.startswith('lo')]
        noeth = False
        if not 'eth0'in [a for a, ip in ifaces]:
            noeth = True
        ems = [a for a, ip in ifaces if a.startswith('em')]
        rpnem = 'em1'
        if noeth and ems:
            rpnem = ems[-1]
        for iface, ips in ifaces:
            # filter out v6 addresses
            ips = [a for a in ips if ':' not in a]
            if ips:
                if not default_ip:
                    default_ip = ips[0]
                if (iface == 'eth1') and devhost:
                    devhost_ip = ips[0]
                if providers_['have_rpn'] and (iface in ['eth1', rpnem]):
                    # configure rpn with dhcp
                    forced_ifs[iface] = {}
        if not default_ip:
            default_ip = '127.0.0.1'
        # hosts managment via pillar
        data['makinahosts'] = makinahosts = []
        # main hostname
        domain_parts = grains['id'].split('.')
        data['devhost_ip'] = devhost_ip
        data['main_ip'] = _s['mc_utils.get'](
            grainsPref + 'main_ip', default_ip)
        data['hostname'] = _s['mc_utils.get'](
            grainsPref + 'hostname', domain_parts[0])
        default_domain = ''
        if len(domain_parts) > 1:
            default_domain = '.'.join(domain_parts[1:])
        data['domain'] = _s['mc_utils.get'](
            grainsPref + 'domain', default_domain)
        data['fqdn'] = _s['mc_utils.get']('nickname', grains['id'])
        localhosts = []
        slug = data['hostname']
        if data['domain']:
            slug = '{hostname}.{domain} {hostname}'.format(**data)
        localhosts.extend([
           '{1} {0}'.format(slug, data['main_ip']),
           '127.0.1.1 {0}'.format(slug),
           '127.0.0.1 {0}'.format(slug),
           '::1       {0}'.format(slug)])
        data['hosts_list'] = hosts_list = []
        for k, edata in pillar.items():
            if k.endswith('makina-hosts'):
                makinahosts.extend(edata)
        # loop to create a dynamic list of hosts based on pillar content
        hosts_list.extend(localhosts)
        for host in makinahosts:
            ip = host['ip']
            for dnsname in host['hosts'].split():
                hosts_list.append(ip + ' ' + dnsname)
        netdata = _s['mc_utils.defaults'](
            'makina-states.localsettings.network', data)
        netdata['hosts_list'] = _s['mc_utils.uniquify'](netdata['hosts_list'])
        # retro compat
        for imapping in netdata['ointerfaces']:
            for ikey, idata in imapping.items():
                ifname = idata.get('ifname', ikey)
                iconf = netdata['interfaces'].setdefault(ifname, {})
                iconf.update(idata)
        netdata['interfaces'].update(forced_ifs)
        for ifc, data in netdata['interfaces'].items():
            data.setdefault('ifname', ifc)
        # get the order configuration
        # on ubuntu 14.04+ and some distros, copy where biosdevname is true
        # from eth0 to the real network iface
        if noeth:
            for i in range(10):
                ethn = 'eth{0}'.format(i)
                for iface in [a for a in netdata['interfaces']
                              if a.startswith(ethn)]:
                    # handle eth0:0
                    suf = iface.replace(ethn, '')
                    newif = real_ifaces[i][0]
                    ifdata = netdata['interfaces'].pop(iface)
                    ifdata['post_roting'] = ['foo via eth0']
                    for k in [b for b in ifdata]:
                        val = ifdata[k]
                        # handle eth0:0
                        if isinstance(val, basestring):
                            ifdata[k] = val.replace(ethn, newif)
                        # handle pre/post/routing
                        elif isinstance(val, list):
                            newval = []
                            for sube in val:
                                if isinstance(sube, basestring):
                                    sube = sube.replace(ethn, newif)
                                newval.append(sube)
                            ifdata[k] = newval
                    netdata['interfaces'][newif + suf] = ifdata
                for ifacedata in netdata['ointerfaces']:
                    for iface in [a
                                  for a in ifacedata
                                  if a.startswith(ethn)]:
                        # handle eth0:0
                        suf = iface.replace(ethn, '')
                        newif = real_ifaces[i][0]
                        ifdata = ifacedata.pop(iface)
                        for k in [b for b in ifdata]:
                            val = ifdata[k]
                            # handle eth0:0
                            if isinstance(val, basestring):
                                ifdata[k] = val.replace(ethn, newif)
                            # handle pre/post/routing
                            elif isinstance(val, list):
                                newval = []
                                for sube in val:
                                    if isinstance(sube, basestring):
                                        sube = sube.replace(ethn, newif)
                                    newval.append(sube)
                                ifdata[k] = newval
                        ifacedata[newif + suf] = ifdata

        # configure alias interfaces only after real ones ...
        iorder = [a for a in netdata['interfaces'] if ':' not in a]
        iorder += [a for a in netdata['interfaces'] if ':' in a]
        netdata['interfaces_order'] = iorder
        return netdata
    return _settings()


def is_loopback(ip):
    try:
        iaddr = ipaddr.IPAddress(ip)
        return iaddr.is_loopback
    except (Exception,):
        return False


def is_link_local(ip):
    try:
        iaddr = ipaddr.IPAddress(ip)
        return iaddr.is_link_local
    except (Exception,):
        return False


def is_public(ip):
    try:
        iaddr = ipaddr.IPAddress(ip)
        return (
            not iaddr.is_private and
            not iaddr.is_reserved and
            not iaddr.is_link_local and
            not iaddr.is_loopback)
    except (Exception,):
        return True


def ns_whois(name, ttl=24*60*60, cache=True, whois_ttl=60*60*24*30):
    '''
    Make a whois request and return data
    For evident performance questons,
    We cache whois data for one month!'''
    def _do(name, cache):
        data = {'query': None}
        if not HAS_PYWHOIS:
            return data
        try:
            wreg = __salt__[
                'mc_macros.get_local_registry'](
                    'ns_whois_data', registry_format='pack')
            if name in wreg:
                if time.time() >= wreg[name]['t'] + whois_ttl:
                    del wreg[name]
            data = wreg.get(name, {}).get('data', {})
            cdata = wreg.setdefault(name, {})
            cdata.setdefault('t', time.time())
            cdata.setdefault('data', data)
            query = cdata.setdefault('query', {})
            if (
                not query or
                not cache or
                (
                    not query.get('expiration_date') and
                    query['registrar'] not in ['ovh', 'gandi'])
            ):
                for i in range(3):
                    try:
                        qdata = whois.query(name)
                        break
                    except (Exception,) as exc:
                        log.error(traceback.format_exc())
                        log.error('Sleeping/retrying in 5 sec for'
                                  ' {0}'.format(name))
                        time.sleep(5)
                        if i == 2:
                            raise exc
                if qdata:
                    query.update(qdata.__dict__)
                    for a in [a for a in query]:
                        if isinstance(query[a], set):
                            query[a] = [b for b in query[a]]
                        if isinstance(query[a], datetime.datetime):
                            query[a] = query[a].isoformat()
            if (
                query and
                not query.get('expiration_date') and
                query['registrar'] not in ['ovh', 'gandi']
            ):
                found = False
                if query['registrar']:
                    for i in ['ovh', 'gandi']:
                        if i in query['registrar'].lower():
                            found = True
                if not found:
                    whoisdata = __salt__['cmd.run']('whois {0}'.format(name))
                    if 'gandi sas' in whoisdata.lower():
                        query['registrar'] = 'gandi'
                    elif 'name: gandi' in whoisdata:
                        query['registrar'] = 'gandi'
            search_data = {'ovh': ['ovh', 'sys'],
                           'phpnet': ['phpnet'],
                           'gandi': ['gandi'],

                           'online': ['illiad',
                                      'proxad',
                                      'iliad']}
            search_data['sys'] = search_data['ovh']
            for provider, search_terms in search_data.items():
                for i in search_terms:
                    for k, val in six.iteritems(
                        query
                    ):
                        if k in ['registrar']:
                            if val and i in val.lower():
                                data['is_{0}'.format(provider)] = True
                                break
            __salt__['mc_macros.update_local_registry'](
                'ns_whois_data', wreg,
                registry_format='pack')
        except Exception:
            log.error(traceback.format_exc())
            data = {}
        return data
    if cache is False:
        return _do(name, cache)
    else:
        cache_key = 'mc_network.,ns_whois{0}'.format(name)
        return __salt__['mc_utils.memoize_cache'](_do, [name, cache], {}, cache_key, ttl)


def domain_registrar(domain, ttl=24*60*60):
    def _do(domain):
        def _ddo(data):
            for i in ['gandi', 'ovh']:
                if data.get('is_{0}'.format(i)):
                    return i
        data = __salt__['mc_network.ns_whois'](domain)
        ret = _ddo(data)
        if ret:
            return ret
        # if not found, try without cache
        else:
            data = __salt__['mc_network.ns_whois'](domain, cache=False)
            ret = _ddo(data)
            if ret:
                return ret
        data = __salt__['mc_network.ns_whois'](domain, cache=False)
        return 'unkown'
    cache_key = 'mc_network.domain_registrar{0}'.format(domain)
    return __salt__['mc_utils.memoize_cache'](_do, [domain], {}, cache_key, ttl)


def whois_data(ip, ttl=24*60*60, whois_ttl=60*60*24*30):
    '''
    Make a whois request and return data
    For evident performance questons,
    We cache whois data for one month!'''
    def _do(ip_, whois_ttl):
        data = {}
        if not HAS_IPWHOIS:
            return data
        try:
            wreg = __salt__[
                'mc_macros.get_local_registry'](
                    'whois_data', registry_format='pack')
            if ip in wreg:
                if time.time() >= wreg[ip]['t'] + whois_ttl:
                    del wreg[ip]
            data = wreg.get(ip, {}).get('data', {})
            if not data:
                data = IPWhois(ip).lookup()
            cdata = wreg.setdefault(ip, {})
            cdata.setdefault('t', time.time())
            cdata.setdefault('data', data)
            search_data = {'ovh': ['ovh', 'sys'],
                           'phpnet': ['phpnet'],
                           'online': ['proxad',
                                      'illiad',
                                      'iliad']}
            search_data['sys'] = search_data['ovh']
            for provider, search_terms in search_data.items():
                for i in search_terms:
                    for j in data.get('nets', []):
                        for k, val in j.items():
                            if k in ['abuse_emails',
                                     'description',
                                     'handle',
                                     'name']:
                                if val and i in val.lower():
                                    data['is_{0}'.format(provider)] = True
                                    break
            __salt__['mc_macros.update_local_registry'](
                'whois_data', wreg,
                registry_format='pack')
        except Exception:
            log.error(traceback.format_exc())
            data = {}
        return data
    cache_key = 'mc_network.whois_data_{0}'.format(ip)
    return __salt__['mc_utils.memoize_cache'](_do, [ip, whois_ttl], {}, cache_key, ttl)


def is_phpnet(ip):
    data = whois_data(ip)
    return data.get('is_phpnet', False)


def is_online(ip):
    data = whois_data(ip)
    return data.get('is_online', False)


def is_ovh(ip):
    data = whois_data(ip)
    return data.get('is_ovh', False)


def is_sys(ip):
    data = whois_data(ip)
    return data.get('is_sys', data.get('is_ovh', False))


def providers():
    return ['online', 'ovh', 'phpnet', 'sys']


def is_ip(ip):
    return is_valid_ip(ip)


def ext_ip():
    '''
    Return the external IP address
    '''
    check_ips = ('http://ipecho.net/plain',
                 'http://v4.ident.me')

    for url in check_ips:
        try:
            with contextlib.closing(urllib2.urlopen(url, timeout=3)) as req:
                ip_ = req.read().strip()
                if not _ipv4_addr(ip_):
                    continue
            return ip_
        except (urllib2.HTTPError,
                urllib2.URLError,
                socket.timeout):
            continue
    return ''


def have_lxc_if():
    _s = __salt__
    ret = None
    data_net = _s['mc_network.default_net']()
    gifaces = data_net['gifaces']
    if True in ['lxc' in a[0] for a in gifaces]:
        ret = False
    return ret


def have_vpn_if():
    _s = __salt__
    ret = None
    data_net = _s['mc_network.default_net']()
    gifaces = data_net['gifaces']
    if True in [a[0].startswith('tun') for a in gifaces]:
        ret = True
    return ret


def have_docker_if():
    _s = __salt__
    ret = None
    data_net = _s['mc_network.default_net']()
    gifaces = data_net['gifaces']
    if True in ['docker' in a[0] for a in gifaces]:
        ret = True
    return ret


def append_netmask(ip):
    # ipv6 is not supported at the moment
    if ':' in ip:
        return ip
    else:
        chunks = ip.split('.')[:4]
        if len(chunks) < 4:
            while len(chunks[:]) < 4:
                chunks.append('0')
        netm = 32
        if chunks[-1] in ['0', 0]:
            for i in range(4):
                if chunks[4 - (i+1)] in ['0']:
                    netm -= 8
                else:
                    break
            if ip.startswith('172.16'):
                netm = '12'
        netm = "{0}".format(netm)
        net = '.'.join(chunks) + '/' + netm
        return net
# vim:set et sts=4 ts=4 tw=80:
