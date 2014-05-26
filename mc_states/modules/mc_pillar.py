#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import json
import yaml
import copy
# Import python libs
import os
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

log = logging.getLogger(__name__)
DOMAIN_PATTERN = '(@{0})|({0}\\.?)$'


class IPRetrievalError(KeyError):
    ''''''

class NoResultError(KeyError):
    ''''''


def dolog(msg):
    log.error("----------------")
    log.error(msg)
    log.error("----------------")


class IPRetrievalCycleError(IPRetrievalError):
    ''''''

def retrieval_error(exc, fqdn, recurse=None):
    exc.fqdn = fqdn
    if recurse is None:
        recurse = []
    exc.recurse = recurse
    raise exc


def get_fqdn_domains(fqdn):
    domains = []
    if fqdn.endswith('.'):
        fqdn = fqdn[:-1]
    if '.' in fqdn:
        parts = fqdn.split('.')[1:]
        parts.reverse()
        for part in parts:
            if domains:
                part = '{0}.{1}'.format(part, domains[-1])
            domains.append(part)
    return domains

# to be easily mockable in tests while having it cached
def loaddb_do(*a, **kw):
    root = '/srv/mastersalt-pillar'
    db = 'makina-states/database.yaml'
    db = yaml.load(open(os.path.join(root, db)).read())
    for item in db:
        if not isinstance(db[item], (dict, list)):
            raise ValueError('Db is invalid')
    return db

def load_db(ttl=60):
    cache_key = 'mc_pillar.load_db'
    return memoize_cache(__salt__['mc_pillar.loaddb_do'],
                         [], {}, cache_key, ttl)


def query_filter(doc_type, **kwargs):
    db = __salt__['mc_pillar.load_db']()
    docs = db[doc_type]
    if doc_type in ['ipsfo_map',
                    'ips',
                    'ipsfo',
                    'hosts',
                    'passwords_map',
                    'burp_configurations']:
        if 'q' in kwargs:
            try:
                docs = docs[kwargs['q']]
            except KeyError:
                raise NoResultError('{0} -> {1}'.format(doc_type, kwargs['q']))
    return docs


_marker = object()


def query(doc_types, ttl=30, default=_marker, **kwargs):
    skwargs = ''
    try:
        skwargs = json.dumps(kwargs)
    except:
        try:
            skwargs = repr(kwargs)
        except:
            pass
    if not isinstance(doc_types, list):
        doc_types = [doc_types]
    if len(doc_types) == 1:
        try:
            if skwargs:
                cache_key = 'mc_pillar.query_{0}{1}'.format(doc_types[0], skwargs)
                return memoize_cache(query_filter,
                                     [doc_types[0]],
                                     kwargs, cache_key, ttl)
            else:
                return query_filter(doc_types[0], **kwargs)
        except NoResultError:
            if default is not _marker:
                return default
    raise RuntimeError('Invalid invocation')


def query_first(doc_types, ttl=30, **kwargs):
    return query(doc_types, ttl, **kwargs)[0]


def _load_network(ttl=60):
    def _do():
        db = __salt__['mc_pillar.load_db']()
        data = {}
        data['rrs_ttls'] = __salt__['mc_pillar.query']('rrs_ttls')
        data['cnames'] = __salt__['mc_pillar.query']('cnames')
        data['standalone_hosts'] = __salt__['mc_pillar.query']('standalone_hosts')
        data['non_managed_hosts'] = __salt__['mc_pillar.query']('non_managed_hosts')
        data['baremetal_hosts'] = __salt__['mc_pillar.query']('baremetal_hosts')
        data['vms'] = __salt__['mc_pillar.query']('vms')
        data['ips'] = __salt__['mc_pillar.query']('ips')
        data['dns_serials'] = __salt__['mc_pillar.query']('dns_serials')
        data['dns_servers'] = __salt__['mc_pillar.query']('dns_servers')
        data['ipsfo'] = __salt__['mc_pillar.query']('ipsfo')
        data['mx_map'] = __salt__['mc_pillar.query']('mx_map')
        data['ips_map'] = __salt__['mc_pillar.query']('ips_map')
        data['ipsfo_map'] = __salt__['mc_pillar.query']('ipsfo_map')
        data['managed_dns_zones'] = __salt__['mc_pillar.query']('managed_dns_zones')
        data['managed_alias_zones'] = __salt__['mc_pillar.query']('managed_alias_zones')
        return data
    cache_key = 'mc_pillar._load_network'
    return memoize_cache(_do, [], {}, cache_key, ttl)


def ips_for(fqdn,
            ips=None,
            ips_map=None,
            ipsfo=None,
            ipsfo_map=None,
            cnames=None,
            fail_over=None,
            recurse=None,
            ignore_aliases=None,
            ignore_cnames=None,):
    '''
    Get all ip for a domain, try as a FQDN first and then
    try to append the specified domain

        fail_over
            If FailOver records exists and no ip was found, it will take this
            value.
            If failOver exists and fail_over=true, all ips
            will be returned

    Warning this method is tightly tied to load_network_infrastructure
    '''
    resips = []
    if (
        (ips is None)
        or (ips_map is None)
        or (cnames is None)
        or (ipsfo is None)
        or (ipsfo_map is None)
    ):
        data = load_network_infrastructure()
        if cnames is None:
            cnames = data['cnames']
        if ips is None:
            ips = data['ips']
        if ips_map is None:
            ips_map = data['ips_map']
        if ipsfo is None:
            ipsfo = data['ipsfo']
        if ipsfo_map is None:
            ipsfo_map = data['ipsfo_map']
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
            alias_ips = ips_for(alias_fqdn,
                                ips=ips, cnames=cnames, ipsfo=ipsfo,
                                ipsfo_map=ipsfo_map, ips_map=ips_map,
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
            alias_ips = ips_for(alias_cname,
                                ips=ips, cnames=cnames, ipsfo=ipsfo,
                                ipsfo_map=ipsfo_map, ips_map=ips_map,
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
            resips = ips_for(fqdn,
                             ips=ips, cnames=cnames, ipsfo=ipsfo,
                             ipsfo_map=ipsfo_map, ips_map=ips_map,
                             recurse=recurse, fail_over=True)
        # for upper tld , check the @ RECORD
        if (
            (not resips)
            and ((not fqdn.startswith('@'))
                 and (fqdn.count('.') == 1))
        ):
            resips = ips_for("@" + fqdn,
                             ips=ips, cnames=cnames, ipsfo=ipsfo,
                             ipsfo_map=ipsfo_map, ips_map=ips_map,
                             recurse=recurse, fail_over=True)
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


def load_network_infrastructure(ttl=60):
    '''This loads the structure while validating it for
    reverse ip lookups

    Warning this method is tightly tied to ips_for
    '''
    def _do():
        data = _load_network()
        cnames = data['cnames']
        standalone_hosts = data['standalone_hosts']
        non_managed_hosts = data['non_managed_hosts']
        baremetal_hosts = data['baremetal_hosts']
        vms = data['vms']
        ips = data['ips']
        dns_serials = data['dns_serials']
        dns_servers = data['dns_servers']
        ipsfo = data['ipsfo']
        mx_map = data['mx_map']
        ips_map = data['ips_map']
        ipsfo_map = data['ipsfo_map']
        managed_dns_zones = data['managed_dns_zones']
        managed_alias_zones = data['managed_alias_zones']
        # add the nameservers if not configured but a managed zone
        for zone in managed_dns_zones:
            nssz = get_nss_for_zone(zone)
            nsszslaves = nssz['slaves']
            for i, slave in enumerate(nsszslaves):
                # special case
                nsq = 'ns{0}.{1}'.format(i + 1, zone)
                if nsq not in ips_map:
                    ips_map[nsq] = [slave]
                if slave in cnames and nsq not in ips:
                    ips[slave] = ips_for(cnames[slave][:-1],
                                         ips=ips, cnames=cnames, ipsfo=ipsfo,
                                         ipsfo_map=ipsfo_map, ips_map=ips_map,
                                         fail_over=True)
                if nsq in cnames and nsq not in ips:
                    ips[slave] = ips_for(cnames[nsq][:-1],
                                         ips=ips, cnames=cnames, ipsfo=ipsfo,
                                         ipsfo_map=ipsfo_map, ips_map=ips_map,
                                         fail_over=True)
                if nsq in ips_map and nsq not in ips:
                    ips[slave] = ips_for(nsq,
                                         ips=ips, cnames=cnames, ipsfo=ipsfo,
                                         ipsfo_map=ipsfo_map, ips_map=ips_map,
                                         fail_over=True)


        for fqdn in ipsfo:
            if fqdn in ips:
                continue
            ips[fqdn] = ips_for(fqdn,
                                ips=ips, cnames=cnames, ipsfo=ipsfo,
                                ipsfo_map=ipsfo_map, ips_map=ips_map,
                                fail_over=True)

        # ADD A Mappings for aliased ips (manual) or over ip failover
        cvms = OrderedDict()
        for vt, targets in vms.items():
            for target, _vms in targets.items():
                for _vm in _vms:
                    cvms[_vm] = target

        cvalues = cvms.values()
        for host, dn_ip_fos in ipsfo_map.items():
            for ip_fo in dn_ip_fos:
                dn = host.split('.')[0]
                ipfo_dn = ip_fo.split('.')[0]
                ip = ips_for(ip_fo,
                             ips=ips, cnames=cnames, ipsfo=ipsfo,
                             ipsfo_map=ipsfo_map, ips_map=ips_map)[0]
                if host in cvms:
                    phost = cvms[host]
                    pdn = phost.split('.')[0]
                    ahosts = [host,
                              '{0}.{1}.{2}'.format(dn, pdn, ip_fo),
                              '{0}.{1}'.format(dn, ip_fo)]
                else:
                    ahosts = ['{0}.{1}'.format(dn, ip_fo),
                              '{1}.{0}'.format(host, ipfo_dn),
                              'failover.{0}'.format(host)]
                    # only add an A record for a failover ip on something which
                    # is not a vm if this is an host without an entry in
                    # the ip and the vms maps
                    if (
                        (host not in baremetal_hosts
                         and host not in cvalues)
                        and host not in ips
                    ):
                        ahosts.append(host)
                for ahost in ahosts:
                    hostips = ips.setdefault(ahost, [])
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
                ips[vm] = ips_for(vm_host,
                                  ips=ips, cnames=cnames, ipsfo=ipsfo,
                                  ipsfo_map=ipsfo_map, ips_map=ips_map)

        # add all IPS  from aliased ips to main dict
        for fqdn in ips_map:
            if fqdn in ips:
                continue
            ips[fqdn] = ips_for(fqdn,
                                ips=ips, cnames=cnames, ipsfo=ipsfo,
                                ipsfo_map=ipsfo_map, ips_map=ips_map)

        nss = get_nss()['all']
        mxs = []
        for servers in mx_map.values():
            for server in servers:
                mxs.append(server)

        # for:
        #   - @ failover mappings
        #   - nameservers
        #   - mx
        # add a A record # where normally we would end up with a CNAME
        for fqdn in ipsfo_map:
            if (fqdn.startswith('@')) or (fqdn in mxs) or (fqdn in nss):
                if fqdn not in ips:
                    ips[fqdn] = ips_for(fqdn,
                                        ips=ips, cnames=cnames, ipsfo=ipsfo,
                                        ipsfo_map=ipsfo_map, ips_map=ips_map,
                                        fail_over=True)
        return data
    cache_key = 'mc_pillar.load_network_infrastructure'
    return memoize_cache(_do, [], {}, cache_key, ttl)


def ip_for(fqdn, fail_over=None):
    '''
    Get an ip for a domain, try as a FQDN first and then
    try to append the specified domain

        fail_over
            If FailOver records exists and no ip was found, it will take this
            value.
            If failOver exists and fail_over=true, all ips
            will be returned
    '''
    return ips_for(fqdn, fail_over=fail_over)[0]


def rr_entry(fqdn, targets, priority='10', record_type='A'):
    db = load_network_infrastructure()
    rrs_ttls = db['rrs_ttls']
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


def rr_a(fqdn, fail_over=None, ttl=60):
    '''
    Search for explicit A record(s) (fqdn/ip) record on the inputed mappings

        fail_over
            If FailOver records exists and no ip was found, it will take this
            value.
            If failOver exists and fail_over=true, all ips
            will be returned
    '''
    def _do(fqdn, fail_over):
        ips = ips_for(fqdn, fail_over=fail_over)
        return rr_entry(fqdn, ips)
    cache_key = 'mc_pillar.rrs_a_{0}_{1}_{2}'.format(domain, fqdn, fail_over)
    return memoize_cache(_do, [fqdn, fail_over], {}, cache_key, ttl)


def rrs_mx_for(domain, ttl=60):
    '''Return all configured NS records for a domain'''
    def _do(domain):
        db = load_network_infrastructure()
        rrs_ttls = db['rrs_ttls']
        mx_map = db['mx_map']
        ips = db['ips']
        all_rrs = OrderedDict()
        servers = mx_map.get(domain, {})
        for fqdn in servers:
            rrs = all_rrs.setdefault(fqdn, [])
            dfqdn = fqdn
            if not dfqdn.endswith('.'):
                dfqdn += '.'
            for rr in rr_entry(
                '@', [dfqdn],
                priority=servers[fqdn].get('priority', '10'),
                record_type='MX'
            ).split('\n'):
                if rr not in rrs:
                    rrs.append(rr)
        rr = filter_rr_str(all_rrs)
        return rr
    cache_key = 'mc_pillar.rrs_mx_for_{0}'.format(domain)
    return memoize_cache(_do, [domain], {}, cache_key, ttl)


def whitelisted(ttl=60):
    '''Return all configured NS records for a domain'''
    def _do():
        db = load_network_infrastructure()
        allow = query('default_allowed_ips_names')
        w = []
        for fqdn in allow:
            for ip in [a for a in ips_for(fqdn) if not a in w]:
                w.append(ip)
        return w
    cache_key = 'mc_pillar.whitelisted'
    return memoize_cache(_do, [], {}, cache_key, ttl)


def filter_rr_str(all_rrs):
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


def rrs_txt_for(domain, ttl=60):
    '''Return all configured NS records for a domain'''
    def _do(domain):
        rrs_ttls = query('rrs_ttls')
        rrs_txts = query('rrs_txt')
        all_rrs = OrderedDict()
        domain_re = re.compile(DOMAIN_PATTERN.format(domain),
                               re.M | re.U | re.S | re.I)
        for rrscols in rrs_txts:
            for fqdn, rrs in rrscols.items():
                if domain_re.search(fqdn):
                    txtrrs = all_rrs.setdefault(fqdn, [])
                    if isinstance(rrs, basestring):
                        rrs = [rrs]
                    dfqdn = fqdn
                    if not dfqdn.endswith('.'):
                        dfqdn += '.'
                    for rr in rr_entry(
                        fqdn, ['"{0}"'.format(r) for r in rrs],
                        rrs_ttls,
                        record_type='TXT'
                    ).split('\n'):
                        if rr not in txtrrs:
                            txtrrs.append(rr)
        rr = filter_rr_str(all_rrs)
        return rr
    cache_key = 'mc_pillar.rrs_txt_for_{0}'.format(domain)
    return memoize_cache(_do, [domain], {}, cache_key, ttl)


def get_slaves_for(id_, ttl=60):
    def _do(id_):
        allslaves = {'z': {}, 'all': []}
        for zone in query('managed_dns_zones'):
            zi = get_nss_for_zone(zone)
            if id_ == zi['master']:
                slaves = allslaves['z'].setdefault(zone, [])
                for fqdn in zi['slaves']:
                    if not fqdn in allslaves['all']:
                        allslaves['all'].append(fqdn)
                    if not fqdn in slaves:
                        slaves.append(fqdn)
        allslaves['all'].sort()
        return allslaves
    cache_key = 'mc_pillar.get_slaves_zones_for_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_slaves_zones_for(id_, ttl=60):
    def _do(id_):
        zones = {}
        for zone in query('managed_dns_zones'):
            zi = get_nss_for_zone(zone)
            if id_ in zi['slaves']:
                zones[zone] = zi['master']
        return zones
    cache_key = 'mc_pillar.get_slaves_zones_for_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_nss(ttl=60):
    def _do():
        dns_servers = {
            'all': [],
            'masters': [],
            'slaves': [],
        }
        dbdns_servers = query('dns_servers')
        for domain, servers_types in dbdns_servers.items():
            for typ_, servers in servers_types.items():
                if not isinstance(servers, list):
                    servers = [servers]
                typ_ = {
                    'master': 'masters'
                }.get(typ_, typ_)
                for s in servers:
                    if s not in dns_servers['all']:
                        dns_servers['all'].append(s)
                    if s not in dns_servers[typ_]:
                        dns_servers[typ_].append(s)
        for a in ['all', 'masters']:
            dns_servers[a].sort()
        return dns_servers
    cache_key = 'mc_pillar.get_nss'
    return memoize_cache(_do, [], {}, cache_key, ttl)


def get_nss_for_zone(id_, ttl=60):
    def _do(id_):
        managed_dns_zones = query('managed_dns_zones')
        dns_servers = query('dns_servers')
        if id_ not in managed_dns_zones:
            raise ValueError('{0} is not managed'.format(id_))
        master = dns_servers.get(id_, {'master': None}).get('master', None)
        slaves = dns_servers.get(id_, {'slaves': []}).get('slaves', [])
        if not master:
            master = dns_servers['default']['master']
        if not slaves:
            slaves = dns_servers['default']['slaves']
        if not slaves:
            slaves = [master]
        if not master and not slaves:
            raise ValueError('no ns for {0}'.format(id_))
        return {'master': master,
                'slaves': slaves}
    cache_key = 'mc_pillar.get_nss_for_zone_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def rrs_ns_for(domain, ttl=60):
    '''Return all configured NS records for a domain'''
    def _do(domain):
        db = load_network_infrastructure()
        rrs_ttls = db['rrs_ttls']
        ips = db['ips']
        all_rrs = OrderedDict()
        servers = get_nss_for_zone(domain)
        for ix, fqdn in enumerate(servers['slaves']):
            # ensure NS A mapping is there
            ns_map = 'ns{0}.{1}'.format(ix + 1, domain)
            assert ips[ns_map] == ips_for(fqdn)
            rrs = all_rrs.setdefault(fqdn, [])
            dfqdn = ns_map
            if not dfqdn.endswith('.'):
                dfqdn += '.'
            for rr in rr_entry(
                '@', [dfqdn], rrs_ttls,
                record_type='NS'
            ).split('\n'):
                if rr not in rrs:
                    rrs.append(rr)
        rr = filter_rr_str(all_rrs)
        return rr
    cache_key = 'mc_pillar.rrs_ns_for_{0}'.format(domain)
    return memoize_cache(_do, [domain], {}, cache_key, ttl)


def rrs_a_for(domain, ttl=60):
    '''Return all configured A records for a domain'''
    def _do(domain):
        db = load_network_infrastructure()
        rrs_ttls = db['rrs_ttls']
        ips = db['ips']
        all_rrs = OrderedDict()
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
        rr = filter_rr_str(all_rrs)
        return rr
    cache_key = 'mc_pillar.rrs_a_for_{0}'.format(domain)
    return memoize_cache(_do, [domain], {}, cache_key, ttl)


def rrs_raw_for(domain, ttl=60):
    '''Return all configured TXT records for a domain'''
    def _do(domain):
        # add all A from simple ips
        db = load_network_infrastructure()
        rrs_raw = query('rrs_raw')
        ips = db['ips']
        all_rrs = OrderedDict()
        domain_re = re.compile(DOMAIN_PATTERN.format(domain),
                               re.M | re.U | re.S | re.I)
        for fqdn in rrs_raw:
            if domain_re.search(fqdn):
                rrs = all_rrs.setdefault(fqdn, [])
                for rr in rrs_raw[fqdn]:
                    if rr not in rrs:
                        rrs.append(rr)
        rr = filter_rr_str(all_rrs)
        return rr
    cache_key = 'mc_pillar.rrs_raw_for_{0}'.format(domain)
    return memoize_cache(_do, [domain], {}, cache_key, ttl)


def rrs_cnames_for(domain, ttl=60):
    '''Return all configured CNAME records for a domain'''
    def _do(domain):
        db = load_network_infrastructure()
        managed_dns_zones = db['managed_dns_zones']
        rrs_ttls = db['rrs_ttls']
        ipsfo = db['ipsfo']
        ipsfo_map = db['ipsfo_map']
        ips_map = db['ips_map']
        cnames = db['cnames']
        ips = db['ips']
        all_rrs = OrderedDict()
        domain_re = re.compile(DOMAIN_PATTERN.format(domain),
                               re.M | re.U | re.S | re.I)

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
                    if (
                        tcname.endswith(domain)
                        and (
                            tcname in ips_map
                            or tcname in ipsfo_map
                            or tcname in ipsfo
                        )
                    ):
                        checks.append(tcname)
                for test in checks:
                    # raise exc if not found
                    # but only if we manage the domain of the targeted
                    # rr
                    try:
                        ips_for(test, fail_over=True)
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
                entry = '{0} {1} CNAME {2}'.format(
                    dcname, ttl, rr)
                if entry not in rrs:
                        rrs.append(entry)
        rr = filter_rr_str(all_rrs)
        return rr
    cache_key = 'mc_pillar.rrs_cnames_for_{0}'.format(domain)
    return memoize_cache(_do, [domain], {}, cache_key, ttl)


def serial_for(domain,
               serial=None,
               autoinc=True):
    '''Get the serial for a DNS zone

    If serial is given: we take that as a value
    Else:
        - the serial defaults to 'YYYYMMDD01'
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
    def _do(domain, serial=None, ttl=60):
        db = __salt__['mc_pillar.load_network_infrastructure']()
        serials = db['dns_serials']
        # load the local pillar dns registry
        dns_reg = __salt__['mc_macros.get_local_registry'](
            'dns_serials')
        if serials is None:
            serials = OrderedDict()
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
    return _do(domain, serial)


def rrs_for(domain):
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
        rrs_ns_for(domain) + '\n' +
        rrs_txt_for(domain) + '\n' +
        rrs_raw_for(domain) + '\n' +
        rrs_mx_for(domain) + '\n' +
        rrs_a_for(domain) + '\n' +
        rrs_cnames_for(domain)
    )
    return rr


def get_ns(domain):
    return get_nss_for_zone(domain)[0]


def get_db_infrastructure_maps(ttl=60):
    '''Return a struct::

         {'bms': {'xx-1.yyy.net': ['lxc'],
                  'xx-4.yyy.net': ['lxc']},
         'vms': {'zz.yyy': {'target': 'xx.yyy.net',
                            'vt': 'kvm'},
                 'vv.yyy.net': {'target': 'xx.yyy.net',
                                'vt': 'kvm'},}}
    '''
    def _do():
        lbms = __salt__['mc_pillar.query']('baremetal_hosts')
        bms = OrderedDict()
        vms = OrderedDict()
        for lbm in lbms:
            bms.setdefault(lbm, [])
        for vt, targets in __salt__['mc_pillar.query']('vms').items():
            for target, lvms in targets.items():
                vts = bms.setdefault(target, [])
                if not vt in vts:
                    vts.append(vt)
                if target not in bms:
                    bms.append(target)
                for vm in lvms:
                    vms.update({vm: {'target': target,
                                     'vt': vt}})
        data = {'bms': bms,
                'non_managed_hosts': query('non_managed_hosts'),
                'vms': vms}
        return data
    cache_key = 'mc_pillar.get_db_infrastructure_maps'
    return memoize_cache(_do, [], {}, cache_key, ttl)


def get_ldap_configuration(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do(id_, sysadmins=None):
        configuration_settings = __salt__[
            'mc_pillar.query']('ldap_configurations')
        data = copy.deepcopy(configuration_settings['default'])
        if id_ in configuration_settings:
            data = __salt__['mc_utils.dictupdate'](data, configuration_settings[id_])
        return data
    cache_key = 'mc_pillar.get_ldap_configuration{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_configuration(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do(id_, sysadmins=None):
        configuration_settings = __salt__['mc_pillar.query']('configurations')
        data = copy.deepcopy(configuration_settings['default'])
        if id_ in configuration_settings:
            data = __salt__['mc_utils.dictupdate'](data, configuration_settings[id_])
        return data
    cache_key = 'mc_pillar.get_global_settings_{0}'.format(id_)
    log.error(cache_key)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_mail_configuration(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do(id_, sysadmins=None):
        mail_settings = __salt__['mc_pillar.query']('mail_configurations')
        data = copy.deepcopy(mail_settings['default'])
        if id_ in mail_settings:
            data = __salt__['mc_utils.dictupdate'](data, mail_settings[id_])
        return data
    cache_key = 'mc_pillar.get_mail_configuration_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_snmpd_settings(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do(id_, sysadmins=None):
        snmpd_settings = __salt__['mc_pillar.query']('snmpd_settings')
        data = copy.deepcopy(snmpd_settings['default'])
        if id_ in snmpd_settings:
            data = __salt__['mc_utils.dictupdate'](data, snmpd_settings[id_])
        return data
    cache_key = 'mc_pillar.get_snmpd_settings_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_shorewall_settings(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do(id_, sysadmins=None):
        qry = __salt__['mc_pillar.query']
        allowed_ips = []
        default_allowed_ips_names = qry('default_allowed_ips_names')
        shorewall_overrides = qry('shorewall_overrides')
        for n in default_allowed_ips_names:
            for ip in __salt__['mc_pillar.ips_for'](n):
                if not ip in allowed_ips:
                    allowed_ips.append(ip)
        allowed_to_ping = allowed_ips[:]
        allowed_to_ntp = allowed_ips[:]
        allowed_to_snmp = allowed_ips[:]
        allowed_to_ssh = allowed_ips[:]
        infra = get_db_infrastructure_maps()
        vms = infra['vms']
        # configure shorewall for a particular host
        # if at least one ip is natted
        # make sure localnets are allowed for ssh to work
        if id_ in vms:
            vms_ips = ips_for(id_)
            hosts_ips = ips_for(vms[id_]['target'])
            for ip in vms_ips:
                if ip in hosts_ips:
                    allowed_to_ssh.extend(
                        ['172.16.0.0/12',
                         '192.168.0.0/24',
                         '10.0.0.0/8'])
        sallowed_ips_to_ssh = 'net:'+','.join(allowed_to_ssh)
        sallowed_ips_to_ping = 'net:'+','.join(allowed_to_ping)
        sallowed_ips_to_snmp = 'net:'+','.join(allowed_to_snmp)
        sallowed_ips_to_ntp = 'net:'+','.join(allowed_to_ntp)

        shw_params = {
          'makina-states.services.firewall.shorewall': True,
          'makina-states.services.firewall.shorewall.params.RESTRICTED_SSH': sallowed_ips_to_ssh,
          'makina-states.services.firewall.shorewall.params.RESTRICTED_PING': sallowed_ips_to_ping,
          'makina-states.services.firewall.shorewall.params.RESTRICTED_SNMP': sallowed_ips_to_snmp,
          'makina-states.services.firewall.shorewall.params.RESTRICTED_NTP': sallowed_ips_to_ntp,
          'makina-states.services.firewall.shorewall.no_snmp': False,
          'makina-states.services.firewall.shorewall.no_ldap': False,
        }
        ips = load_network_infrastructure()['ips']
        # dot not scale !
        #for ip in ips:
        #    sip = __salt__['mc_localsettings.get_pillar_sw_ip'](ip)
        #    k = 'makina-states.services.firewall.shorewall.params.00_IP_{0}'.format(sip)
        #    shw_params[k] = ",".join(ips[ip])
        for param, value in shorewall_overrides.get(id_, {}).items():
            param = 'makina-states.services.firewall.shorewall.' + param
            shw_params[param] = value
        return shw_params
    cache_key = 'mc_pillar.get_shorewall_settings_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_sysadmins_keys(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do(id_, sysadmins=None):
        sysadmins_keys_map = __salt__['mc_pillar.query']('sysadmins_keys_map')
        keys_map = __salt__['mc_pillar.query']('keys_map')
        skeys = []
        sysadmins = sysadmins_keys_map.get(
            id_, sysadmins_keys_map['default'])
        if 'infra' not in sysadmins:
            sysadmins.append('infra')
        for k in sysadmins:
            keys = keys_map.get(k, [])
            for key in keys:
                if key not in skeys:
                    skeys.append(key)
        return skeys
    cache_key = 'mc_pillar.get_sysadmin_keys_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_passwords(id_, ttl=60):
    '''Return user/password mappings for a particular host from
    a global pillar passwords map'''
    if not id_:
        id_ = __opts__['id']
    def _do(id_):
        passwords_map = __salt__['mc_pillar.query']('passwords_map')
        passwords = {'clear': {}, 'crypted': {}}
        passwords['clear']['root'] = passwords_map['root'][id_]
        passwords['clear']['sysadmin'] = passwords_map.get('sysadmin', {}).get(
            id_, passwords['clear']['root'])
        for user, data in passwords_map.items():
            if user in ['root', 'sysadmin']:
                continue
            if isinstance(data, dict):
                for host, data in data.items():
                    if host not in [id_]:
                        continue
                    if isinstance(data, basestring):
                        passwords['clear'][user] = data
        for user, password in passwords['clear'].items():
            passwords['crypted'][user] = __salt__['mc_utils.unix_crypt'](password)
        return passwords
    cache_key = 'mc_pillar.get_passwords_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_ssh_groups(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do(id_, sysadmins=None):
        db_ssh_groups = __salt__['mc_pillar.query']('ssh_groups')
        ssh_groups = db_ssh_groups.get(
            id_,  db_ssh_groups['default'])
        for group in db_ssh_groups['default']:
            if group not in ssh_groups:
                ssh_groups.append(group)
        return ssh_groups
    cache_key = 'mc_pillar.get_ssh_groups_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_sudoers(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do(id_, sysadmins=None):
        sudoers_map = __salt__['mc_pillar.query']('sudoers_map')
        sudoers = sudoers_map.get(id_, [])
        for s in sudoers_map['default']:
            if s not in (sudoers + ['infra']):
                sudoers.append(s)
        return sudoers
    cache_key = 'mc_pillar.get_sudoers_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_top_variables(ttl=15):
    def _do():
        data = {}
        data.update(get_db_infrastructure_maps())
        return data
    cache_key = 'mc_pillar.get_top_variables'
    return memoize_cache(_do, [], {}, cache_key, ttl)


def is_dns_slave(id_, ttl=60):
    def _do(id_):
        servers = get_nss_for_zone(id_)
    cache_key = 'mc_pillar.is_dns_slave_{9}'.format(id_)
    return memoize_cache(_do, [], {}, cache_key, ttl)

def is_dns_master(id_, ttl=60):
    def _do(id_):
        return
    cache_key = 'mc_pillar.is_dns_master_{9}'.format(id_)
    return memoize_cache(_do, [], {}, cache_key, ttl)


def get_makina_states_variables(id_, ttl=60):
    def _do(id_):
        data = {}
        data.update(get_top_variables())
        is_vm = id_ in data['vms']
        is_bm = id_ in data['bms']
        data['dns_servers'] = query('dns_servers')
        data.update({
            'id': id_,
            'eid': id_.replace('.', '+'),
            'is_bm': is_bm,
            'is_vm': is_vm,
            'managed': (
                (is_vm or is_bm)
                and id_ not in __salt__['mc_pillar.query']('non_managed_hosts')
            ),
            'vts_sls': {'kvm': 'makina-states.kvmvm',
                        'lxc': 'makina-states.lxccontainer'},
            'bm_vts_sls': {'lxc': 'makina-states.lxc'}
        })
        data['msls'] = 'minions.{eid}'.format(**data)
        return data
    cache_key = 'mc_pillar.get_makina_states_variables_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


# vim:set et sts=4 ts=4 tw=80:
