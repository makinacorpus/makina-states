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
# Import python libs
import logging
import copy
import mc_states.utils
import re
from salt.utils.odict import OrderedDict

__name = 'network'

log = logging.getLogger(__name__)


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
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        grains = __grains__
        pillar = __pillar__
        data = {'interfaces': {}, 'ointerfaces': []}
        grainsPref = 'makina-states.localsettings.'
        providers = __salt__['mc_provider.settings']()
        # Does the network base config file have to be managed via that
        # See makina-states.localsettings.network
        # Compat for the first test!
        data['networkManaged'] = (
            saltmods['mc_utils.get']('makina-states.network_managed', False)
            or saltmods['mc_utils.get'](grainsPref + 'network.managed', False))

        # ip managment
        default_ip = None
        ifaces = grains['ip_interfaces'].items()
        ifaces.sort(key=sort_ifaces)
        devhost_ip = None
        forced_ifs = {}
        devhost = __salt__['mc_nodetypes.registry']()['is']['devhost']
        for iface, ips in ifaces:
            if ips:
                if not default_ip:
                    default_ip = ips[0]
                if (iface == 'eth1') and devhost:
                    devhost_ip = ips[0]
                if providers['have_rpn'] and (iface in ['eth1', 'em1']):
                    # configure rpn with dhcp
                    forced_ifs[iface] = {}
        if not default_ip:
            default_ip = '127.0.0.1'
        # hosts managment via pillar
        data['makinahosts'] = makinahosts = []
        # main hostname
        domain_parts = grains['id'].split('.')
        data['devhost_ip'] = devhost_ip
        data['main_ip'] = saltmods['mc_utils.get'](
            grainsPref + 'main_ip', default_ip)
        data['hostname'] = saltmods['mc_utils.get'](
            grainsPref + 'hostname', domain_parts[0])
        default_domain = ''
        if len(domain_parts) > 1:
            default_domain = '.'.join(domain_parts[1:])
        data['domain'] = saltmods['mc_utils.get'](
            grainsPref + 'domain', default_domain)
        data['fqdn'] = saltmods['mc_utils.get']('nickname', grains['id'])
        if data['domain']:
            data['makinahosts'].append({
                'ip': '{main_ip}'.format(**data),
                'hosts': '{hostname} {hostname}.{domain}'.format(**data)
            })
        data['hosts_list'] = hosts_list = []
        for k, edata in pillar.items():
            if k.endswith('makina-hosts'):
                makinahosts.extend(edata)
        # -loop to create a dynamic list of hosts based on pillar content
        for host in makinahosts:
            ip = host['ip']
            for dnsname in host['hosts'].split():
                hosts_list.append(ip + ' ' + dnsname)
        netdata = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.network', data)
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
        netdata['interfaces_order'] = [a for a in netdata['interfaces']]
        return netdata
    return _settings()


def ips_for(fqdn, ips, ipsfo, ipsfo_map, fail_over=None):
    '''
    Get all ip for a domain, try as a FQDN first and then
    try to append the specified domain

        ips
            mapping FQDN / list of ips
        ipsfo_map
            mapping FQDN / list of failover identifiers (fqdn)
        ipsfo
            a mapping IPFO FQDN / list of associated ips
        fail_over
            If FailOver records exists and no ip was found, it will take this
            value.
            If failOver exists and fail_over=true, all ips
            will be returned
    '''
    resips = []
    if fqdn in ips:
        resips.extend(ips[fqdn][:])
    if fail_over:
        if (fqdn in ipsfo):
            resips.append(ipsfo[fqdn])
        for ipfo in ipsfo_map.get(fqdn, []):
            resips.append(ipsfo[ipfo])
    if not resips:
        # allow fail over fallback if nothing was specified
        if fail_over is None:
            return ips_for(fqdn, ips, ipsfo, ipsfo_map, fail_over=True)
        else:
            raise KeyError('ips not found for {0}'.format(fqdn))
    resips = __salt__['mc_utils.uniquify'](resips)
    return resips


def ip_for(fqdn, ips, ipsfo, ipsfo_map, fail_over=None):
    '''
    Get an ip for a domain, try as a FQDN first and then
    try to append the specified domain

        ips
            mapping FQDN / list of ips
        ipsfo_map
            mapping FQDN / list of failover identifiers (fqdn)
        ipsfo
            a mapping IPFO FQDN / list of associated ips
        fail_over
            If FailOver records exists and no ip was found, it will take this
            value.
            If failOver exists and fail_over=true, all ips
            will be returned
    '''
    return ips_for(fqdn, ips, ipsfo, ipsfo_map, fail_over=fail_over)[0]


def rr_a(fqdn, ips, ipsfo, ipsfo_map, rrs_ttls, fail_over=None):
    '''
    Search for explicit A record(s) (fqdn/ip) record on the inputed mappings

        ips
            mapping FQDN / list of ips
        ipsfo_map
            mapping FQDN / list of failover identifiers (fqdn)
        ipsfo
            a mapping IPFO FQDN / list of associated ips
        fail_over
            If FailOver records exists and no ip was found, it will take this
            value.
            If failOver exists and fail_over=true, all ips
            will be returned
    '''
    ips = ips_for(fqdn, ips, ipsfo, ipsfo_map, fail_over=fail_over)
    fqdn_entry = fqdn
    if fqdn.startswith('@'):
        fqdn_entry = '@'
    elif not fqdn.endswith('.'):
        fqdn_entry += '.'
    ttl = rrs_ttls.get(fqdn_entry,  '')
    rr = '{0} {1} A {2}\n'.format(fqdn_entry, ttl, ips[0])
    for ip in ips[1:]:
        ttl = rrs_ttls.get(fqdn_entry,  '')
        rr += '       {0} {1} A {2}\n'.format(fqdn_entry,
                                              ttl,
                                              ip)
    rr = '\n'.join([a for a in rr.split('\n') if a.strip()])
    return rr


DOMAIN_PATTERN = '(@{0})|({0}\\.?)$'


def rrs_a_for(domain, ips, ipsfo, ipsfo_map,
              baremetal_hosts, vms, rrs_ttls):
    '''Return all configured A records for a domain'''
    all_rrs = {}
    domain_re = re.compile(DOMAIN_PATTERN.format(domain),
                           re.M | re.U | re.S | re.I)

    # add all A from simple ips
    for fqdn in ips:
        if domain_re.search(fqdn):
            rrs = all_rrs.setdefault(fqdn, [])
            for rr in rr_a(
                fqdn, ips, ipsfo, ipsfo_map, rrs_ttls
            ).split('\n'):
                if rr not in rrs:
                    rrs.append(rr)
    # add all A from failover ips
    for fqdn in ipsfo:
        if domain_re.search(fqdn):
            rrs = all_rrs.setdefault(fqdn, [])
            for rr in rr_a(
                fqdn, ips, ipsfo, ipsfo_map, rrs_ttls,
                fail_over=True
            ).split('\n'):
                if rr not in rrs:
                    rrs.append(rr)
    rr = ''
    for row in all_rrs.values():
        rr += '\n'.join(row) + '\n'
    # add all domain baremetal mapped on failovers
    rr = [re.sub('^ *', '       ', a)
          for a in rr.split('\n') if a.strip()]
    rr = __salt__['mc_utils.uniquify'](rr)
    rr.sort()
    rr = re.sub('^ *', '       ', '\n'.join(rr), re.X | re.S | re.U | re.M)
    return rr


def rrs_cnames_for(domain, ips, ipsfo, ipsfo_map,
                   baremetal_hosts, vms, cnames, rrs_ttls):
    '''Return all configured CNAME records for a domain'''
    all_rrs = {}
    domain_re = re.compile(DOMAIN_PATTERN.format(domain),
                           re.M | re.U | re.S | re.I)
    # add all domain ips
    for cname, rr in cnames.items():
        if domain_re.search(cname):
            rrs = all_rrs.setdefault(cname, [])
            dcname = cname
            if (
                (not cname.endswith('.'))
                and cname.endswith(domain)
            ):
                dcname = '{0}.'.format(dcname)
            ttl = rrs_ttls.get(cname,  '')
            entry = '{0} {1} CNAME {2}'.format(dcname,
                                               ttl,
                                               rr)
            if entry not in rrs:
                rrs.append(entry)
    cvms = []
    for vt, targets in vms.items():
        for target, _vms in targets.items():
            cvms.extend(_vms)
    for host, dn_ip_fos in ipsfo_map.items():
        if domain_re.search(host):
            if (
                host in baremetal_hosts
                or host in cvms
            ):
                dn = host.split('.{0}'.format(domain))[0]
                for ip_fo in dn_ip_fos:
                    ttl = rrs_ttls.get(host,  '')
                    if ip_fo.endswith(domain):
                        ip_fo += '.'
                    entry = '{0}.{1} {2} CNAME {3}'.format(
                        dn, ip_fo, ttl, ip_fo)
                    if entry not in rrs:
                        rrs.append(entry)
            else:
                for dn_ip_fo in dn_ip_fos:
                    dcname = host
                    if (
                        (not dcname.endswith('.'))
                        and dcname.endswith(domain)
                    ):
                        dcname = '{0}.'.format(dcname)
                    if dcname.startswith('@') and len(dcname) > 1:
                        continue
                    ttl = rrs_ttls.get(host,  '')
                    entry = '{0} {1} CNAME {2}'.format(dcname, ttl, dn_ip_fo)
                    if entry not in rrs:
                        rrs.append(entry)
    rr = ''
    for row in all_rrs.values():
        rr += '\n'.join(row) + '\n'
    # add all domain baremetal mapped on failovers
    rr = [re.sub('^ *', '       ', a)
          for a in rr.split('\n') if a.strip()]
    rr.sort()
    rr = __salt__['mc_utils.uniquify'](rr)
    rr = '\n'.join(rr)
    return rr


def rrs_for(domain, ips, ipsfo, ipsfo_map, baremetal_hosts, vms, cnames, rrs_ttls):
    '''Return all configured records for a domain

    For the moment:

        - A records
        - CNAME records

    '''
    rr = (
        rrs_a_for(domain, ips, ipsfo, ipsfo_map,
                  baremetal_hosts, vms, rrs_ttls) +
        '\n' +
        rrs_cnames_for(domain, ips, ipsfo, ipsfo_map,
                       baremetal_hosts, vms, cnames, rrs_ttls)
    )
    return rr


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# vim:set et sts=4 ts=4 tw=80:
