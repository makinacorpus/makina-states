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
import time
from pprint import pformat
import copy
import mc_states.utils
import datetime
import re
from salt.utils.odict import OrderedDict
import traceback

from mc_states.utils import memoize_cache


class IPRetrievalError(KeyError):
    ''''''


class IPRetrievalCycleError(IPRetrievalError):
    ''''''


def retrieval_error(exc, fqdn, recurse=None):
    exc.fqdn = fqdn
    if recurse is None:
        recurse = []
    exc.recurse = recurse
    raise exc


__name = 'network'

log = logging.getLogger(__name__)
DOMAIN_PATTERN = '(@{0})|({0}\\.?)$'


def get_fqdn_domains(fqdn):
    domains = []
    if '.' in fqdn:
        parts = fqdn.split('.')[1:]
        parts.reverse()
        for part in parts:
            if domains:
                part = '{0}.{1}'.format(part, domains[-1])
            domains.append(part)
    return domains


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


def ips_for(fqdn, ips, ips_map, ipsfo,
            ipsfo_map, cnames, fail_over=None,
            recurse=None,
            ignore_aliases=None,
            ignore_cnames=None,):
    '''
    Get all ip for a domain, try as a FQDN first and then
    try to append the specified domain

        ips
            mapping FQDN / list of ips
        ips_map
            mapping FQDN / FQDN which has a real ip associated
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
    if recurse is None:
        recurse = []
    if ignore_cnames is None:
        ignore_cnames = []
    if ignore_aliases is None:
        ignore_aliases = []
    if fqdn not in recurse:
        recurse.append(fqdn)

    # first, search for real baremetal ips
    if fqdn in ips:
        resips.extend(ips[fqdn][:])

    # then failover
    if fail_over:
        if (fqdn in ipsfo):
            resips.append(ipsfo[fqdn])
        for ipfo in ipsfo_map.get(fqdn, []):
            resips.append(ipsfo[ipfo])

    # then for ips which are duplicated among other dns names
    for alias_fqdn in ips_map.get(fqdn, []):
        # avoid recursion
        for _fqdn in [fqdn, alias_fqdn]:
            if _fqdn in ignore_aliases or _fqdn in ignore_cnames:
                sfqdn = ''
                if _fqdn != fqdn:
                    sfqdn = '/{0}'.format(_fqdn)
                    retrieval_error(
                        IPRetrievalCycleError((
                            'Recursion from alias {0}{1}:\n'
                            ' recurse: {4}\n'
                            ' ignored aliases: {3}\n'
                            ' ignored cnames: {2}\n'
                        ).format(fqdn, sfqdn, ignore_cnames,
                                 ignore_aliases, recurse)),
                        fqdn, recurse=recurse)
        ignore_aliases.append(alias_fqdn)
        try:
            alias_ips = ips_for(alias_fqdn, ips, ips_map,
                                ipsfo, ipsfo_map, cnames,
                                fail_over=fail_over,
                                recurse=recurse,
                                ignore_aliases=ignore_aliases,
                                ignore_cnames=ignore_cnames)
        except RuntimeError:
            retrieval_error(
                IPRetrievalCycleError(
                    'Recursion(r) from alias {0}:\n'
                    ' recurse: {3}\n'
                    ' ignored cnames: {1}\n'
                    ' ignored aliases: {2}\n'.format(
                        alias_fqdn, ignore_cnames, ignore_aliases,
                        recurse)),
                fqdn, recurse=recurse)
        if alias_ips:
            resips.extend(alias_ips)
        for _fqdn in [fqdn, alias_fqdn]:
            for ignore in [ignore_aliases, ignore_cnames]:
                if _fqdn in ignore:
                    ignore.pop(ignore.index(_fqdn))
    for ignore in [ignore_aliases]:
        if fqdn in ignore:
            ignore.pop(ignore.index(fqdn))

    # and if still no ip found but cname is present,
    # try to get ip from cname
    if (not resips) and fqdn in cnames:
        alias_cname = cnames[fqdn]
        if alias_cname.endswith('.'):
            alias_cname = alias_cname[:-1]
        # avoid recursion
        for _fqdn in [alias_cname]:
            if _fqdn in ignore_aliases or _fqdn in ignore_cnames:
                sfqdn = ''
                if _fqdn != fqdn:
                    sfqdn = '/{0}'.format(_fqdn)
                retrieval_error(
                    IPRetrievalCycleError(
                        'Recursion from cname {0}{1}:\n'
                        ' recurse: {4}\n'
                        ' ignored cnames: {2}\n'
                        ' ignored aliases: {3}\n'.format(
                            fqdn, sfqdn, ignore_cnames,
                            ignore_aliases, recurse)),
                    fqdn, recurse=recurse)
        ignore_cnames.append(alias_cname)
        try:
            alias_ips = ips_for(alias_cname, ips, ips_map,
                                ipsfo, ipsfo_map, cnames,
                                fail_over=fail_over,
                                recurse=recurse,
                                ignore_aliases=ignore_aliases,
                                ignore_cnames=ignore_cnames)
        except RuntimeError:
            retrieval_error(
                IPRetrievalCycleError(
                    'Recursion(r) from cname {0}:\n'
                    ' recurse: {3}\n'
                    ' ignored cnames: {1}\n'
                    ' ignored aliases: {2}\n'.format(
                        alias_cname, ignore_cnames,
                        ignore_aliases, recurse)),
                fqdn, recurse=recurse)
        if alias_ips:
            resips.extend(alias_ips)
        for _fqdn in [fqdn, alias_cname]:
            for ignore in [ignore_aliases, ignore_cnames]:
                if _fqdn in ignore:
                    ignore.pop(ignore.index(_fqdn))

    if not resips:
        # allow fail over fallback if nothing was specified
        if fail_over is None:
            resips = ips_for(fqdn, ips, ips_map, ipsfo, ipsfo_map,
                             cnames, recurse=recurse, fail_over=True)
        # for upper tld , check the @ RECORD
        if (
            (not resips)
            and ((not fqdn.startswith('@'))
                 and (fqdn.count('.') == 1))
        ):
            resips = ips_for("@" + fqdn, ips, ips_map, ipsfo, ipsfo_map,
                             cnames, recurse=recurse, fail_over=True)
        if not resips:
            msg = '{0}\n'.format(fqdn)
            if len(recurse) > 1:
                msg += 'recurse: {0}\n'.format(recurse)
            retrieval_error(IPRetrievalError(msg), fqdn, recurse=recurse)

    for ignore in [ignore_aliases, ignore_cnames]:
        if fqdn in ignore:
            ignore.pop(ignore.index(fqdn))
    resips = __salt__['mc_utils.uniquify'](resips)
    return resips


def ip_for(fqdn, ips, ips_map, ipsfo, ipsfo_map, cnames, fail_over=None):
    '''
    Get an ip for a domain, try as a FQDN first and then
    try to append the specified domain

        ips
            mapping FQDN / list of ips
        ips_map
            mapping FQDN / FQDN which has a real ip associated
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
    return ips_for(fqdn, ips, ips_map, ipsfo, ipsfo_map, cnames, fail_over=fail_over)[0]


def rr_entry(fqdn, targets, rrs_ttls, priority='10', record_type='A'):
    if record_type in ['MX']:
        priority = ' {0}'.format(priority)
    else:
        priority = ''
    fqdn_entry = fqdn
    if fqdn.startswith('@'):
        fqdn_entry = '@'
    elif not fqdn.endswith('.'):
        fqdn_entry += '.'
    ttl = rrs_ttls.get(fqdn_entry,  '')
    IN = ''
    if record_type in ['NS', 'MX']:
        IN = ' IN'
    rr = '{0}{1}{2} {3}{4} {5}\n'.format(
        fqdn_entry, ttl, IN, record_type, priority, targets[0])
    for ip in targets[1:]:
        ttl = rrs_ttls.get(fqdn_entry,  '')
        if ttl:
            ttl = ' {0}'.format(ttl)
        rr += '       {0}{1}{2} {3}{4} {5}\n'.format(
            fqdn_entry, ttl, IN, record_type, priority, ip)
    rr = '\n'.join([a for a in rr.split('\n') if a.strip()])
    return rr


def rr_a(fqdn, ips, ips_map, ipsfo, ipsfo_map,
         cnames, rrs_ttls, fail_over=None):
    '''
    Search for explicit A record(s) (fqdn/ip) record on the inputed mappings

        ips
            mapping FQDN / list of ips
        ips_map
            mapping FQDN / FQDN which has a real ip associated
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
    ips = ips_for(fqdn, ips, ips_map,
                  ipsfo, ipsfo_map, cnames, fail_over=fail_over)
    return rr_entry(fqdn, ips, rrs_ttls)


def load_all_ips(ips, ips_map, ipsfo, ipsfo_map,
                 baremetal_hosts, vms, cnames, rrs_ttls,
                 ns_map, mx_map):
    if ips.get('__loaded__', False):
        return
    for fqdn in ipsfo:
        if fqdn in ips:
            continue
        ips[fqdn] = ips_for(fqdn, ips, ips_map, ipsfo, ipsfo_map,
                            cnames, fail_over=True)

    # ADD A Mappings for aliased ips (manual) or over ip failover
    cvms = {}
    for vt, targets in vms.items():
        for target, _vms in targets.items():
            for _vm in _vms:
                cvms[_vm] = target

    for host, dn_ip_fos in ipsfo_map.items():
        for ip_fo in dn_ip_fos:
            if host in ips:
                host = 'failover.{0}'.format(host, ip_fo)
            hostips = ips.setdefault(host, [])
            for ip in ips_for(ip_fo, ips, ips_map, ipsfo, ipsfo_map,
                              cnames):
                if ip not in hostips:
                    hostips.append(ip)

    # For all vms:
    # if the vm still does not have yet an ip resolved
    # map a A directly to the host
    # If the host is mapped on an ip failover
    # add a transitionnal cname for the vm to be mounted on this ipfo
    # eg: direct
    # <vm>.<host>.<domain>
    # eg: failover
    # <vm>.<host>.<ipfo_dn>.<domain>
    for vm, vm_host in cvms.items():
        if vm not in ips:
            ips[vm] = ips_for(vm_host, ips, ips_map, ipsfo, ipsfo_map,
                              cnames)

    # add all IPS  from aliased ips to main dict
    for fqdn in ips_map:
        if fqdn in ips:
            continue
        ips[fqdn] = ips_for(fqdn, ips, ips_map, ipsfo, ipsfo_map,
                            cnames)
    nss = []
    mxs = []
    for servers in mx_map.values():
        for server in servers:
            mxs.append(server)
    for servers in ns_map.values():
        for server in servers:
            nss.append(server)
    # for:
    #   - @ failover mappings
    #   - nameservers
    #   - mx
    # add a A record # where normally we would end up with a CNAME
    for fqdn in ipsfo_map:
        if (fqdn.startswith('@')) or (fqdn in mxs) or (fqdn in nss):
            if fqdn not in ips:
                ips[fqdn] = ips_for(fqdn, ips, ips_map, ipsfo, ipsfo_map,
                                    cnames, fail_over=True)
    ips['__loaded__'] = '1.2.3.4'


def rrs_mx_for(domain, ips, ips_map, ipsfo, ipsfo_map,
               baremetal_hosts, vms, cnames, rrs_ttls,
               rrs_raw, ns_map, mx_map):
    '''Return all configured NS records for a domain'''
    load_all_ips(ips, ips_map, ipsfo, ipsfo_map,
                 baremetal_hosts, vms, cnames, rrs_ttls,
                 ns_map, mx_map)
    all_rrs = {}
    servers = mx_map.get(domain, {})
    for fqdn in servers:
        rrs = all_rrs.setdefault(fqdn, [])
        dfqdn = fqdn
        if not dfqdn.endswith('.'):
            dfqdn += '.'
        for rr in rr_entry(
            '@', [dfqdn], rrs_ttls,
            priority=servers[fqdn].get('priority', '10'),
            record_type='MX'
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


def rrs_ns_for(domain, ips, ips_map, ipsfo, ipsfo_map,
               baremetal_hosts, vms, cnames, rrs_ttls,
               rrs_raw, ns_map, mx_map):
    '''Return all configured NS records for a domain'''
    load_all_ips(ips, ips_map, ipsfo, ipsfo_map,
                 baremetal_hosts, vms, cnames, rrs_ttls,
                 ns_map, mx_map)
    all_rrs = {}
    servers = ns_map.get(domain, {})
    for fqdn in servers:
        rrs = all_rrs.setdefault(fqdn, [])
        dfqdn = fqdn
        if not dfqdn.endswith('.'):
            dfqdn += '.'
        for rr in rr_entry(
            '@', [dfqdn], rrs_ttls,
            priority=servers[fqdn].get('priority', '10'),
            record_type='NS'
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


def rrs_a_for(domain, ips, ips_map, ipsfo, ipsfo_map,
              baremetal_hosts, vms, cnames, rrs_ttls,
              ns_map, mx_map):
    '''Return all configured A records for a domain'''
    load_all_ips(ips, ips_map, ipsfo, ipsfo_map,
                 baremetal_hosts, vms, cnames, rrs_ttls,
                 ns_map, mx_map)
    all_rrs = {}
    domain_re = re.compile(DOMAIN_PATTERN.format(domain),
                           re.M | re.U | re.S | re.I)
    # add all A from simple ips
    for fqdn in ips:
        if domain_re.search(fqdn):
            rrs = all_rrs.setdefault(fqdn, [])
            for rr in rr_entry(
                fqdn, ips[fqdn], rrs_ttls
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


def rrs_raw_for(domain, ips, ips_map, ipsfo, ipsfo_map,
                baremetal_hosts, vms, cnames, rrs_ttls, rrs_raw,
                ns_map, mx_map):
    '''Return all configured TXT records for a domain'''
    # add all A from simple ips
    load_all_ips(ips, ips_map, ipsfo, ipsfo_map,
                 baremetal_hosts, vms, cnames, rrs_ttls,
                 ns_map, mx_map)
    all_rrs = {}
    domain_re = re.compile(DOMAIN_PATTERN.format(domain),
                           re.M | re.U | re.S | re.I)
    for fqdn in rrs_raw:
        if domain_re.search(fqdn):
            rrs = all_rrs.setdefault(fqdn, [])
            for rr in rrs_raw[fqdn]:
                if rr not in rrs:
                    rrs.append(rr)
    rr = ''
    for row in all_rrs.values():
        rr += '\n'.join(row) + '\n'
    # add all domain baremetal mapped on failovers
    rr = [re.sub('^ *', '       ', a)
          for a in rr.split('\n') if a.strip()]
    rr = __salt__['mc_utils.uniquify'](rr)
    rr = re.sub('^ *', '       ', '\n'.join(rr), re.X | re.S | re.U | re.M)
    return rr


def rrs_cnames_for(domain, ips, ips_map, ipsfo, ipsfo_map,
                   baremetal_hosts, vms, cnames, rrs_ttls,
                   ns_map, mx_map, managed_dns_zones):
    '''Return all configured CNAME records for a domain'''
    load_all_ips(ips, ips_map, ipsfo, ipsfo_map,
                 baremetal_hosts, vms, cnames, rrs_ttls,
                 ns_map, mx_map)
    all_rrs = {}
    domain_re = re.compile(DOMAIN_PATTERN.format(domain),
                           re.M | re.U | re.S | re.I)
    end_domain_re = re.compile(
        '\\.{0}$'.format(domain), re.M | re. S | re. U | re.I)
    # if this is a baremetal host or a vm
    # this add automaticly a cname on each tied
    # failover ip in the form <host>.<ipfo>.<domain>
    # and <vm>.<host>.<ipfo>.<domain>

    # # FOR NOW GIVE UP CNAME ON IP FAILOVERS,
    # # CAUSING MORE HARM THAN GOOD
    # for host, dn_ip_fos in ipsfo_map.items():
    #     if domain_re.search(host):
    #         if (
    #             host in baremetal_hosts
    #             or host in cvms
    #         ):
    #             dn = host.split('.{0}'.format(domain))[0]
    #             for ip_fo in dn_ip_fos:
    #                 if ip_fo.endswith(domain):
    #                     ip_fo += '.'
    #                 possible_host = ''
    #                 if host in cvms:
    #                     cvms_records.append(host)
    #                     possible_host = cvms[host]
    #                 if possible_host:
    #                     possible_host = '.{0}'.format(
    #                         end_domain_re.sub('', possible_host))
    #                 cnn = '{0}{2}.{1}'.format(dn, ip_fo, possible_host)
    #                 if not cnn.endswith('.'):
    #                     cnn += '.'
    #                 cnames[cnn[:-1]] = ip_fo
    #                 if host in cvms:
    #                     cnames['{0}.{1}'.format(dn, ip_fo[:-1])] = cnn
    #                     dnipfo = '{0}.{1}'.format(dn, ip_fo)
    #                     if not dnipfo.endswith('.'):
    #                         dnipfo += '.'
    #                     cnames['{0}.{1}'.format(dn, domain)] = dnipfo
    #         else:
    #             for dn_ip_fo in dn_ip_fos:
    #                 dcname = host
    #                 if (
    #                     (not dcname.endswith('.'))
    #                     and dcname.endswith(domain)
    #                 ):
    #                     dcname = '{0}.'.format(dcname)
    #                 # if @ is handled on an ip failover, add a A record
    #                 # so this is handled in rr_a and not here
    #                 if dcname.startswith('@'):
    #                     continue
    #                 cname_tgt = dn_ip_fo
    #                 # for other records, use a cname
    #                 if not cname_tgt.endswith('.'):
    #                     cname_tgt += '.'
    #                 if dcname.endswith('.'):
    #                     dcname = dcname[:-1]
    #                 cnames[dcname] = cname_tgt

    # For all vms:
    # if the vm was not mounted using an ip failover
    # map a cname directly to the host
    # If the host is mapped on an ip failover
    # add a transitionnal cname for the vm to be mounted on this ipfo
    # eg: direct
    # <vm>.<host>.<domain>
    # eg: failover
    # <vm>.<host>.<ipfo_dn>.<domain>
    # for vm, vm_host in cvms.items():
    #     if domain_re.search(vm):
    #         if vm not in cvms_records:
    #             cvms_records.append(vm)
    #             dn = vm.split('.{0}'.format(domain))[0]
    #             if vm_host in ipsfo_map:
    #                 fo_dn = ipsfo_map[vm_host][0]
    #                 host_dn = vm_host.split('.{0}'.format(domain))[0]
    #                 vm_host = '{0}.{1}'.format(host_dn, fo_dn)
    #             if not vm_host.endswith('.'):
    #                 vm_host += '.'
    #             # first cname in the form <vm>.<host>.<domain> -> <host>
    #             cnn = '{0}.{1}'.format(dn, end_domain_re.sub('', vm_host))
    #             if cnn.endswith('.'):
    #                 cnn = cnn[:-1]
    #             cnames[cnn] = vm_host
    #             # first cname in the form <vm>.<host>.<domain>
    #             # 2nd  cname in the form <vm>.<domain> -> <vm>.<host>.<domain>
    #             if not cnn.endswith('.'):
    #                 cnn += '.'
    #             cnames['{0}.{1}'.format(dn, domain)] = cnn

    # filter out CNAME which have also A records
    for cname in [a for a in cnames]:
        if cname in ips:
            cnames.pop(cname)

    # add all cnames
    for cname, rr in cnames.items():
        tcname, trr = cname, rr
        if tcname.endswith('.'):
            tcname = tcname[:-1]
        if trr.endswith('.'):
            trr = trr[:-1]
        if domain_re.search(cname):
            # on the same domain validate if the cname SOURCE or
            # ENDPOINT are tied to real ip
            # and raise exception if not found
            checks = []
            if trr.endswith(domain):
                checks.append(trr)
                if tcname.endswith(domain):
                    checks.append(tcname)
            for test in checks:
                # raise exc if not found
                # but only if we manage the domain of the targeted
                # rr
                try:
                    ips_for(test, ips, ips_map, ipsfo,
                            ipsfo_map, cnames, fail_over=True)
                except IPRetrievalError, exc:
                    do_raise = False
                    fqdmns = get_fqdn_domains(exc.fqdn)
                    for dmn in fqdmns:
                        if dmn in managed_dns_zones:
                            do_raise = True
                    if do_raise:
                        raise
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


def serial_for(domain,
               serials=None,
               serial=None,
               autoinc=True):
    '''Get the serial for a DNS zone
    This function is cached one

    If serial is given: we take that as a value
    Else:
        - the serials defaults to 'YYYYMMDD01'
        - We try to load the serial from db and if
          it is superior to default, we use it
        - We then load a local autosave file
          with mappings of domain/dns serials

            - If serial is found and autoinc:
                this local stored serial is autoincremented
                by 1

            - if this local value is greater than the
              current serial, this becomes the serial,
    '''
    def _do(domain, serials=None, serial=None, ttl=60):
        # load the local pillar dns registry
        dns_reg = __salt__['mc_macros.get_local_registry'](
            'dns_serials')
        if serials is None:
            serials = {}
        override = True
        if serial is None:
            override = False
            serial = int(
                datetime.datetime.now().strftime('%Y%m%d01'))
        # serial ttl update
        # we can only update the serial after a TTL
        try:
            db_serial = int(serials.get(domain, serial))
        except (ValueError, TypeError):
            db_serial = serial
        tnow = time.time()
        ttl_key = '{0}__ttl__'.format(domain)
        stale = False
        try:
            stale = abs(int(tnow) - int(dns_reg[ttl_key])) > ttl
        except (KeyError, ValueError, TypeError):
            stale = True
        if not override:
            if db_serial > serial:
                serial = db_serial
            if domain in dns_reg:
                try:
                    dns_reg_serial = int(dns_reg[domain])
                    if stale and autoinc:
                        dns_reg_serial += 1
                except (ValueError, TypeError):
                    dns_reg_serial = serial
                if dns_reg_serial > serial:
                    serial = dns_reg_serial
        dns_reg[domain] = serial
        # only update the ttl on expiraton or creation
        if stale:
            dns_reg[ttl_key] = time.time()
        __salt__['mc_macros.update_local_registry'](
            'dns_serials', dns_reg)
        return serial
    return _do(domain, serials, serial)
    #cache_key = 'dnsserials_t_{0}'.format(domain)
    #return memoize_cache(
    #    _do, [domain, serials, serial], {}, cache_key, 60)


def rrs_for(domain, ips, ips_map, ipsfo, ipsfo_map,
            baremetal_hosts, vms, cnames, rrs_ttls, rrs_raw,
            ns_map, mx_map, managed_dns_zones):
    '''Return all configured records for a domain
    take all rr found for the "ips" & "ipsfo" tables for domain
        - Make NS records for everything in ns_map
        - Make MX records for everything in mx_map
        - Make A records for everything in ips
        - Make A records for everything in ips_map
        - Make A records for everything in ipsfo
        - Make CNAME records for baremetal or vms if they are
          in the ipsfo_map hashtable.
        - Add the related TTL for each record matched inside
          the rrs_ttls hashstable
    '''
    rr = (
        rrs_ns_for(
            domain, ips, ips_map, ipsfo, ipsfo_map,
            baremetal_hosts, vms, cnames, rrs_ttls, rrs_raw,
            ns_map, mx_map,
        ) +
        '\n' +
        rrs_mx_for(
            domain, ips, ips_map, ipsfo, ipsfo_map,
            baremetal_hosts, vms, cnames, rrs_ttls, rrs_raw,
            ns_map, mx_map,
        ) +
        '\n' +
        rrs_raw_for(
            domain, ips, ips_map, ipsfo, ipsfo_map,
            baremetal_hosts, vms, cnames, rrs_ttls, rrs_raw,
            ns_map, mx_map
        ) +
        '\n' +
        rrs_a_for(
            domain, ips, ips_map, ipsfo, ipsfo_map,
            baremetal_hosts, vms, cnames, rrs_ttls,
            ns_map, mx_map) +
        '\n' +
        rrs_cnames_for(
            domain, ips, ips_map, ipsfo, ipsfo_map,
            baremetal_hosts, vms, cnames, rrs_ttls,
            ns_map, mx_map, managed_dns_zones)
    )
    return rr


def get_ns(domain, ns_map):
    return ns_map[domain].keys()[0]


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# vim:set et sts=4 ts=4 tw=80:
