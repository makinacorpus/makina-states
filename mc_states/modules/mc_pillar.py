#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import json
import copy
# Import python libs
import os
import socket
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
import random
import string
log = logging.getLogger(__name__)


DOMAIN_PATTERN = '(@{0})|({0}\\.?)$'
DOTTED_DOMAIN_PATTERN = '((^{0}\\.?$)|(\\.(@{0})|({0}\\.?)))$'


def yaml_load(*args, **kw):
    return __salt__['mc_utils.cyaml_load'](*args, **kw)


def yaml_dump(*args, **kw):
    return __salt__['mc_utils.cyaml_dump'](*args, **kw)


def generate_password(length=None):
    return __salt__['mc_utils.generate_password'](length)


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
    dbpath = os.path.join(
        __opts__['pillar_roots']['base'][0],
        'database.yaml')
    with open(dbpath) as fic:
        db = yaml_load(fic.read())
    for item in db:
        types = (dict, list)
        if item in ['format']:
            types = (int,)
        if not isinstance(db[item], types):
            raise ValueError('Db is invalid for {0}'.format(item))
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
        data['cloud_cn_attrs'] = __salt__['mc_pillar.query']('cloud_cn_attrs')
        data['cloud_vm_attrs'] = __salt__['mc_pillar.query']('cloud_vm_attrs')
        data['non_managed_hosts'] = __salt__['mc_pillar.query']('non_managed_hosts')
        data['baremetal_hosts'] = __salt__['mc_pillar.query']('baremetal_hosts')
        data['vms'] = __salt__['mc_pillar.query']('vms')
        data['ldap_maps'] = __salt__['mc_pillar.query']('ldap_maps')
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
            ignore_cnames=None, **kw):
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
        try:
            if alias_cname.endswith('.'):
                alias_cname = alias_cname[:-1]
        except:
            log.error('CNAMES')
            log.error(cnames)
            raise
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
    def _do_nt():
        data = _load_network()
        cnames = data['cnames']
        standalone_hosts = data['standalone_hosts']
        non_managed_hosts = data['non_managed_hosts']
        cloud_vm_attrs = data['cloud_vm_attrs']
        cloud_cn_attrs = data['cloud_cn_attrs']
        baremetal_hosts = data['baremetal_hosts']
        vms = data['vms']
        ips = data['ips']
        dns_serials = data['dns_serials']
        dns_servers = data['dns_servers']
        ldap_maps = data['ldap_maps']
        ipsfo = data['ipsfo']
        mx_map = data['mx_map']
        ips_map = data['ips_map']
        ipsfo_map = data['ipsfo_map']
        managed_dns_zones = data['managed_dns_zones']
        managed_alias_zones = data['managed_alias_zones']
        # add the nameservers if not configured but a managed zone
        for zone in managed_dns_zones:
            nssz = get_nss_for_zone(zone)
            for nsq, slave in nssz['slaves'].items():
                # special case
                if nsq not in ips_map:
                    ips_map[nsq] = [slave]
                if slave in cnames and nsq not in ips:
                    ips[slave] = [ip_for(cnames[slave][:-1],
                                         ips=ips, cnames=cnames, ipsfo=ipsfo,
                                         ipsfo_map=ipsfo_map, ips_map=ips_map,
                                         fail_over=True)]
                if nsq in cnames and nsq not in ips:
                    ips[slave] = [ip_for(cnames[nsq][:-1],
                                         ips=ips, cnames=cnames, ipsfo=ipsfo,
                                         ipsfo_map=ipsfo_map, ips_map=ips_map,
                                         fail_over=True)]
                if nsq in ips_map and nsq not in ips:
                    ips[slave] = [ip_for(nsq,
                                         ips=ips, cnames=cnames, ipsfo=ipsfo,
                                         ipsfo_map=ipsfo_map, ips_map=ips_map,
                                         fail_over=True)]

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
                if vm in ips_map:
                    ips[vm] = ips_for(vm,
                                      ips=ips, cnames=cnames, ipsfo=ipsfo,
                                      ipsfo_map=ipsfo_map, ips_map=ips_map)
                else:
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
        #
        # tie extra domains of vms to a A record
        #
        for vm, _data in cloud_vm_attrs.items():
            domains = _data.get('domains', [])
            if not isinstance(domains, list):
                continue
            for domain in domains:
                dips = ips.setdefault(domain, [])
                # never append an ip of a vm is it is already defined
                if len(dips):
                    continue
                for ip in ips_for(vm,
                                  ips=ips, cnames=cnames, ipsfo=ipsfo,
                                  ipsfo_map=ipsfo_map, ips_map=ips_map,
                                  fail_over=True):
                    if ip not in dips:
                        dips.append(ip)
        return data
    cache_key = 'mc_pillar.load_network_infrastructure'
    return memoize_cache(_do_nt, [], {}, cache_key, ttl)


def ip_for(fqdn, *args, **kw):
    '''
    Get an ip for a domain, try as a FQDN first and then
    try to append the specified domain

        fail_over
            If FailOver records exists and no ip was found, it will take this
            value.
            If failOver exists and fail_over=true, all ips
            will be returned
    '''
    return ips_for(fqdn, *args, **kw)[0]


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


def whitelisted(dn, ttl=60):
    '''Return all configured NS records for a domain'''
    def _do_whitel(dn):
        db = load_network_infrastructure()
        allow = query('default_allowed_ips_names')
        allow = allow.get(dn, allow['default'])
        w = []
        for fqdn in allow:
            for ip in [a for a in ips_for(fqdn) if not a in w]:
                w.append(ip)
        return w
    cache_key = 'mc_pillar.whitelisted_{0}'.format(dn)
    return memoize_cache(_do_whitel, [dn], {}, cache_key, ttl)


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
        domain_re = re.compile(DOTTED_DOMAIN_PATTERN.format(domain),
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


def get_ldap(ttl=60):
    '''Get a map of relationship between name servers
    that is used in the pillar to attribute roles
    and configuration to name servers

    This return a mapping in the form::

        {
            all: [list of all nameservers],
            masters: mapping of mappings {master: [list of related slaves]},
            slaves: mapping of mappings {slave: [list of related masters]},
        }

    For each zone, if slaves are declared without master,
    the default masters would be added as master for this zone if any defaults.

    '''
    def _do_getldap():
        db = load_network_infrastructure()
        data = OrderedDict()
        data.setdefault('masters', OrderedDict())
        data.setdefault('slaves', OrderedDict())
        default = db['ldap_maps'].get('default', OrderedDict())
        for kind in ['masters', 'slaves']:
            for server, adata in db['ldap_maps'].get(kind,
                                                     OrderedDict()).items():
                sdata = data[kind][server] = copy.deepcopy(adata)
                for k, val in default.items():
                    sdata.setdefault(k, val)
        return data
    cache_key = 'mc_pillar.getldap'
    return memoize_cache(_do_getldap, [], {}, cache_key, ttl)


def get_slapd_conf(id_, ttl=60):
    '''
    Return pillar information to configure makina-states.services.dns.slapd
    '''
    def _do_getldap(id_):
        is_master = is_ldap_master(id_)
        is_slave = is_ldap_slave(id_)
        if is_master and is_slave:
            raise ValueError(
                'Cant be at the same time master and ldap slave: {0}'.format(id_))
        if not is_master and not is_slave:
            raise ValueError(
                'Choose between master and ldap slave: {0}'.format(id_))
        conf = get_ldap()
        if is_master:
            data = conf['masters'][id_]
            data['mode'] = 'master'
        elif is_slave:
            data = conf['slaves'][id_]
            data['mode'] = 'slave'
        ssl_domain = data.setdefault('cert_domain', id_)
        # maybe generate and get the ldap certificates info
        ssl_infos = __salt__['mc_ssl.ca_ssl_certs'](
            ssl_domain, as_text=True)[0]
        data.setdefault('tls_cacert', ssl_infos[0])
        data.setdefault('tls_cert', ssl_infos[1])
        data.setdefault('tls_key', ssl_infos[2])
        return data
    cache_key = 'mc_pillar.get_ldap_conf_for_{0}'.format(id_)
    return memoize_cache(_do_getldap, [id_], {}, cache_key, ttl)


def is_ldap_slave(id_, ttl=60):
    def _do(id_):
        if id_ in __salt__['mc_pillar.get_ldap']()['slaves']:
            return True
        return False
    cache_key = 'mc_pillar.is_ldap_slave_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def is_ldap_master(id_, ttl=60):
    def _do(id_):
        if id_ in __salt__['mc_pillar.get_ldap']()['masters']:
            return True
        return False
    cache_key = 'mc_pillar.is_ldap_master_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_nss(ttl=60):
    '''Get a map of relationship between name servers
    that is used in the pillar to attribute roles
    and configuration to name servers

    This return a mapping in the form::

        {
            all: [list of all nameservers],
            masters: mapping of mappings {master: [list of related slaves]},
            slaves: mapping of mappings {slave: [list of related masters]},
        }

    For each zone, if slaves are declared without master,
    the default masters would be added as master for this zone if any defaults.

    '''
    def _do_getnss():
        dns_servers = {'all': [],
                       'masters': OrderedDict(),
                       'slaves': OrderedDict()}
        dbdns_zones = query('managed_dns_zones')
        for domain in dbdns_zones:
            master = get_ns_master(domain)
            slaves = get_ns_slaves(domain)
            slaves_targets = slaves.values()
            for server in [master] + slaves_targets:
                if server not in dns_servers['all']:
                    dns_servers['all'].append(server)
            master_slaves = dns_servers['masters'].setdefault(master, [])
            for target in slaves_targets:
                if target not in master_slaves:
                    master_slaves.append(target)
                target_masters = dns_servers['slaves'].setdefault(target, [])
                if master not in target_masters:
                    target_masters.append(master)
        dns_servers['all'].sort()
        return dns_servers
    cache_key = 'mc_pillar.get_nss'
    return memoize_cache(_do_getnss, [], {}, cache_key, ttl)


def get_ns_master(id_, dns_servers=None, default=None, ttl=60):
    '''Grab masters in this form::

        dns_servers:
            zoneid_dn:
                master: fqfn
    '''
    def _do_get_ns_master(id_, dns_servers=None, default=None):
        managed_dns_zones = query('managed_dns_zones')
        if id_ not in managed_dns_zones:
            raise ValueError('{0} is not managed'.format(id_))
        if not dns_servers:
            dns_servers = query('dns_servers')
        if not default:
            default = dns_servers['default']
        master = dns_servers.get(
            id_, OrderedDict()).get('master', None)
        if not master:
            master = default.get('master', None)
        if not master:
            raise ValueError('No master for {0}'.format(id_))
        if not isinstance(master, basestring):
            raise ValueError(
                '{0} is not a string for dns master {1}'.format(
                    master, id_))
        return master
    cache_key = 'mc_pillar.get_ns_master_{0}'.format(id_)
    return memoize_cache(_do_get_ns_master,
                         [id_, dns_servers, default], {}, cache_key, ttl)


def get_ns_slaves(id_, dns_servers=None, default=None, ttl=60):
    '''Grab slaves in this form::

        dns_servers:
            zoneid_dn:
                slaves:
                    - dn: fqdn
    '''
    def _do_get_ns_slaves(id_, dns_servers=None, default=None):
        managed_dns_zones = query('managed_dns_zones')
        if id_ not in managed_dns_zones:
            raise ValueError('{0} is not managed'.format(id_))
        if not dns_servers:
            dns_servers = query('dns_servers')
        if not default:
            default = dns_servers['default']
        lslaves = dns_servers.get(
            id_, OrderedDict()).get('slaves', OrderedDict())
        if not lslaves:
            lslaves = default.get('slaves', OrderedDict())
        if lslaves and not isinstance(lslaves, list):
            raise ValueError('Invalid format for slaves for {0}'.format(id_))
        for item in lslaves:
            if not isinstance(item, dict):
                raise ValueError('Invalid format for slaves for {0}'.format(id_))
        slaves = OrderedDict()
        for slave in lslaves:
            for nsid in [a for a in slave]:
                target = copy.deepcopy(slave[nsid])
                cnsid = nsid
                if not isinstance(nsid, basestring):
                    raise ValueError(
                        '{0} is not a valid dn for nameserver in '
                        '{1}'.format(nsid, id_))
                if not isinstance(target, basestring):
                    raise ValueError(
                        '{0} is not a valid dn for nameserver target in '
                        '{1}'.format(target, id_))
                if id_ not in nsid:
                    cnsid = '{0}.{1}'.format(nsid, id_)
                slaves[cnsid] = target
        return slaves
    cache_key = 'mc_pillar.get_ns_slaves_{0}'.format(id_)
    return memoize_cache(_do_get_ns_slaves,
                         [id_, dns_servers, default], {}, cache_key, ttl)


def get_nss_for_zone(id_, ttl=60):
    '''Return all masters and slaves for a zone

    If there is a master but no slaves, the master becomes also the only slave
    for that zone

    Slave in makina-states means a name server which is exposed to outside
    world via an NS record.
    '''
    def _do_getnssforzone(id_):
        dns_servers = query('dns_servers')
        master = get_ns_master(id_, dns_servers=dns_servers)
        slaves = get_ns_slaves(id_, dns_servers=dns_servers)
        if not master and not slaves:
            raise ValueError('no ns information for {0}'.format(id_))
        data = {'master': master, 'slaves': slaves}
        return data
    cache_key = 'mc_pillar.get_nss_for_zone_{0}'.format(id_)
    return memoize_cache(_do_getnssforzone, [id_], {}, cache_key, ttl)


def get_slaves_for(id_, ttl=60):
    '''Get all public exposed dns servers slaves
    for a specific dns master
    Return something like::

        {
            all: [all slaves related to this master],
            z: {
                {zone domains: [list of slaves related to this zone]
               }
        }

    '''
    def _do_getslavesfor(id_):
        allslaves = {'z': OrderedDict(), 'all': []}
        for zone in query('managed_dns_zones'):
            zi = get_nss_for_zone(zone)
            if id_ == zi['master']:
                slaves = allslaves['z'].setdefault(zone, [])
                for nsid, fqdn in zi['slaves'].items():
                    if fqdn not in allslaves['all']:
                        allslaves['all'].append(fqdn)
                    if fqdn not in slaves:
                        slaves.append(fqdn)
        allslaves['all'].sort()
        return allslaves
    cache_key = 'mc_pillar.get_slaves_for_{0}'.format(id_)
    return memoize_cache(_do_getslavesfor, [id_], {}, cache_key, ttl)


def get_ns(domain):
    '''Get the first configured public name server for domain'''
    def _do(domain):
        return get_nss_for_zone(domain)[0]
    cache_key = 'mc_pillar.get_ns_{0}'.format(domain)
    return memoize_cache(_do, [domain], {}, cache_key, ttl)


def get_slaves_zones_for(fqdn, ttl=60):
    def _do_getslaveszonesfor(fqdn):
        zones = {}
        for zone in query('managed_dns_zones'):
            zi = get_nss_for_zone(zone)
            if fqdn in zi['slaves'].values():
                zones[zone] = zi['master']
        return zones
    cache_key = 'mc_pillar.get_slaves_zones_for_{0}'.format(fqdn)
    return memoize_cache(_do_getslaveszonesfor, [fqdn], {}, cache_key, ttl)


def rrs_mx_for(domain, ttl=60):
    '''Return all configured NS records for a domain'''
    def _do_mx(domain):
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
    return memoize_cache(_do_mx, [domain], {}, cache_key, ttl)


def rrs_mx_for(domain, ttl=60):
    '''Return all configured NS records for a domain'''
    def _do_mx(domain):
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
    return memoize_cache(_do_mx, [domain], {}, cache_key, ttl)


def rrs_ns_for(domain, ttl=60):
    '''Return all configured NS records for a domain'''
    def _dorrsnsfor(domain):
        db = load_network_infrastructure()
        rrs_ttls = db['rrs_ttls']
        ips = db['ips']
        all_rrs = OrderedDict()
        servers = get_nss_for_zone(domain)
        slaves = servers['slaves']
        if not slaves:
            rrs = all_rrs.setdefault(domain, [])
            rrs.append(
                rr_entry('@', ["{0}.".format(servers['master'])],
                         rrs_ttls, record_type='NS'))
        for ns_map, fqdn in slaves.items():
            # ensure NS A mapping is there
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
    return memoize_cache(_dorrsnsfor, [domain], {}, cache_key, ttl)


def rrs_a_for(domain, ttl=60):
    '''Return all configured A records for a domain'''
    def _dorrsafor(domain):
        db = load_network_infrastructure()
        rrs_ttls = db['rrs_ttls']
        ips = db['ips']
        all_rrs = OrderedDict()
        domain_re = re.compile(DOTTED_DOMAIN_PATTERN.format(domain),
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
    return memoize_cache(_dorrsafor, [domain], {}, cache_key, ttl)


def rrs_raw_for(domain, ttl=60):
    '''Return all configured TXT records for a domain'''
    def _dorrsrawfor(domain):
        # add all A from simple ips
        db = load_network_infrastructure()
        rrs_raw = query('rrs_raw')
        ips = db['ips']
        all_rrs = OrderedDict()
        domain_re = re.compile(DOTTED_DOMAIN_PATTERN.format(domain),
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
    return memoize_cache(_dorrsrawfor, [domain], {}, cache_key, ttl)


def rrs_cnames_for(domain, ttl=60):
    '''Return all configured CNAME records for a domain'''
    def _dorrscnamesfor(domain):
        db = load_network_infrastructure()
        managed_dns_zones = db['managed_dns_zones']
        rrs_ttls = db['rrs_ttls']
        ipsfo = db['ipsfo']
        ipsfo_map = db['ipsfo_map']
        ips_map = db['ips_map']
        cnames = db['cnames']
        ips = db['ips']
        all_rrs = OrderedDict()
        domain_re = re.compile(DOTTED_DOMAIN_PATTERN.format(domain),
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
    return memoize_cache(_dorrscnamesfor, [domain], {}, cache_key, ttl)


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
    def _doserialfor(domain, serial=None, ttl=60):
        db = __salt__['mc_pillar.load_network_infrastructure']()
        serials = db['dns_serials']
        # load the local pillar dns registry
        dns_reg = __salt__['mc_macros.get_local_registry'](
            'dns_serials', registry_format='pack')
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
            'dns_serials', dns_reg, registry_format='pack')
        return serial
    return _doserialfor(domain, serial)


def rrs_for(domain, aslist=False):
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
    if aslist:
        rr = [a.strip() for a in rr.split('\n') if a.strip()]
    return rr


def get_db_infrastructure_maps(ttl=60):
    '''Return a struct::

         {'bms': {'xx-1.yyy.net': ['lxc'],
                  'xx-4.yyy.net': ['lxc']},
         'vms': {'zz.yyy': {'target': 'xx.yyy.net',
                            'vt': 'kvm'},
                 'vv.yyy.net': {'target': 'xx.yyy.net',
                                'vt': 'kvm'},}}
    '''
    def _dogetdbinframaps():
        lbms = __salt__['mc_pillar.query']('baremetal_hosts')
        bms = OrderedDict()
        vms = OrderedDict()
        non_managed_hosts = query('non_managed_hosts')
        cloud_compute_nodes = []
        cloud_vms = []
        for lbm in lbms:
            bms.setdefault(lbm, [])
        for vt, targets in __salt__['mc_pillar.query']('vms').items():
            for target, lvms in targets.items():
                if (
                    target not in non_managed_hosts
                    and target not in cloud_compute_nodes
                ):
                    cloud_compute_nodes.append(target)
                vts = bms.setdefault(target, [])
                if vt not in vts:
                    vts.append(vt)
                if target not in bms:
                    bms.append(target)
                for vm in lvms:
                    if vm not in non_managed_hosts:
                        cloud_vms.append(vm)
                    vms.update({vm: {'target': target,
                                     'vt': vt}})
        data = {'bms': bms,
                'non_managed_hosts': query('non_managed_hosts'),
                'cloud_compute_nodes': cloud_compute_nodes,
                'cloud_vms': cloud_vms,
                'vms': vms}
        return data
    cache_key = 'mc_pillar.get_db_infrastructure_maps'
    return memoize_cache(_dogetdbinframaps, [], {}, cache_key, ttl)


def get_ldap_configuration(id_=None, ttl=60):
    '''
    Ldap client configuration
    '''
    if not id_:
        id_ = __opts__['id']
    def _do_ldap(id_, sysadmins=None):
        configuration_settings = __salt__[
            'mc_pillar.query']('ldap_configurations')
        data = copy.deepcopy(configuration_settings['default'])
        if id_ in configuration_settings:
            data = __salt__['mc_utils.dictupdate'](data, configuration_settings[id_])
        return data
    cache_key = 'mc_pillar.get_ldap_configuration{0}'.format(id_)
    return memoize_cache(_do_ldap, [id_], {}, cache_key, ttl)


def get_configuration(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do_conf(id_, sysadmins=None):
        configuration_settings = __salt__['mc_pillar.query']('configurations')
        data = copy.deepcopy(configuration_settings['default'])
        if id_ in configuration_settings:
            data = __salt__['mc_utils.dictupdate'](data, configuration_settings[id_])
        return data
    cache_key = 'mc_pillar.get_configuration_{0}'.format(id_)
    return memoize_cache(_do_conf, [id_], {}, cache_key, ttl)


def get_mail_configuration(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do_mail(id_, sysadmins=None):
        mail_settings = __salt__['mc_pillar.query']('mail_configurations')
        data = copy.deepcopy(mail_settings['default'])
        if id_ in mail_settings:
            data = __salt__['mc_utils.dictupdate'](data, mail_settings[id_])
        return data
    cache_key = 'mc_pillar.get_mail_configuration_{0}'.format(id_)
    return memoize_cache(_do_mail, [id_], {}, cache_key, ttl)


def get_snmpd_settings(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do_snmpd(id_, sysadmins=None):
        snmpd_settings = __salt__['mc_pillar.query']('snmpd_settings')
        data = copy.deepcopy(snmpd_settings['default'])
        if id_ in snmpd_settings:
            data = __salt__['mc_utils.dictupdate'](data, snmpd_settings[id_])
        return data
    cache_key = 'mc_pillar.get_snmpd_settings_{0}'.format(id_)
    return memoize_cache(_do_snmpd, [id_], {}, cache_key, ttl)


def get_shorewall_settings(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do_sw(id_, sysadmins=None):
        qry = __salt__['mc_pillar.query']
        allowed_ips = __salt__['mc_pillar.whitelisted'](id_)
        shorewall_overrides = qry('shorewall_overrides')
        cfg = get_configuration(id_)
        allowed_to_ping = ['all']
        allowed_to_ntp = allowed_ips[:]
        allowed_to_snmp = allowed_ips[:]
        allowed_to_ssh = allowed_ips[:]
        infra = get_db_infrastructure_maps()
        nvars  = __salt__['mc_pillar.load_network_infrastructure']()
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
        restrict = {'ssh': 'net:'+','.join(allowed_to_ssh),
                    'ping':  'net:'+','.join(allowed_to_ping),
                    'snmp': 'net:'+','.join(allowed_to_snmp),
                    'ntp': 'net:'+','.join(allowed_to_ntp)}
        restrict_ssh = cfg.get('manage_ssh_ip_restrictions', False)
        if not restrict_ssh:
            restrict['ssh'] = 'all'
        for param in [a for a in restrict]:
            if ',all' in restrict[param]:
                restrict[param] = 'all'
            if restrict[param] == 'net:all':
                restrict[param] = 'all'
        shw_params = {
            'makina-states.services.firewall.shorewall': True,
            'makina-states.services.firewall.shorewall.no_snmp': False,
            'makina-states.services.firewall.shorewall.no_ldap': False}
        p_param = ('makina-states.services.firewall.'
                   'shorewall.params.RESTRICTED_{0}')
        for param, val in restrict.items():
            shw_params[p_param.format(param.upper())] = val
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
    return memoize_cache(_do_sw, [id_], {}, cache_key, ttl)


def get_removed_keys(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do_removed(id_, removed=None):
        removed_keys_map = __salt__['mc_pillar.query']('removed_keys_map')
        keys_map = __salt__['mc_pillar.query']('keys_map')
        skeys = []
        removed = removed_keys_map.get(
            id_, removed_keys_map['default'])
        for k in removed:
            keys = keys_map.get(k, [])
            for key in keys:
                if key not in skeys:
                    skeys.append(key)
        return skeys
    cache_key = 'mc_pillar.get_removed_keys{0}'.format(id_)
    return memoize_cache(_do_removed, [id_], {}, cache_key, ttl)


def get_sysadmins_keys(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do_sys_keys(id_, sysadmins=None):
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
    return memoize_cache(_do_sys_keys, [id_], {}, cache_key, ttl)


def delete_password_for(id_, user='root', ttl=60):
    '''Cleanup a password entry from the local password database'''
    if not id_:
        id_ = __opts__['id']
    pw_reg = __salt__['mc_macros.get_local_registry'](
        'passwords_map', registry_format='pack')
    pw_id = pw_reg.setdefault(id_, {})
    store = False
    updated = 'not changed'
    # default sysadmin password is root's one
    if user in pw_id:
        del pw_id[user]
        __salt__['mc_macros.update_local_registry'](
            'passwords_map', pw_reg, registry_format='pack')
        updated = 'removed'
    return updated


def get_password(id_, user='root', ttl=60, regenerate=False, length=12,
                 force=False):
    '''Return user/password mappings for a particular host from
    a global pillar passwords map. Create it if not done'''
    if not id_:
        id_ = __opts__['id']
    def _do_pass(id_, user='root'):
        db_reg = __salt__['mc_pillar.query']('passwords_map')
        db_id = db_reg.setdefault(id_, {})
        pw_reg = __salt__['mc_macros.get_local_registry'](
            'passwords_map', registry_format='pack')
        pw_id = pw_reg.setdefault(id_, {})
        store = False
        pw = db_id.get(user, None)
        # default sysadmin password is root's one
        if pw is None and user == 'sysadmin':
            pw = db_id.get('root', None)
        # if not found, fallback on local database
        if pw is None:
            pw = pw_id.get(user, None)
        if pw is None and user == 'sysadmin':
            pw = pw_id.get('root', None)
        # if still not found, generate and store
        # if regenerate is asked, regenerate only if
        # the password is not coming from the central database
        # but may be present only in the localdb
        if (
            (pw is None)
            or (regenerate and (user not in db_id))
            or force
        ):
            pw = generate_password(length)
            store = True
        pw_id[user] = pw
        db_id[user] = pw
        # store locally passwords
        # and update them on change
        if (user not in pw_id) or (pw_id.get(user, None) != pw):
            store = True
        if store:
            __salt__['mc_macros.update_local_registry'](
                'passwords_map', pw_reg, registry_format='pack')
        cpw = __salt__['mc_utils.unix_crypt'](pw)
        return {'clear': pw,
                'crypted': cpw}
    if force or regenerate:
        return _do_pass(id_, user)
    cache_key = 'mc_pillar.get_passwords_for_{0}_{1}'.format(id_, user)
    return memoize_cache(_do_pass, [id_, user], {}, cache_key, ttl)


def get_passwords(id_, ttl=60):
    '''Return user/password mappings for a particular host from
    a global pillar passwords map
    Take in priority pw from the db map
    But if does not exists in the db, lookup inside the local one
    If stiff non found, generate it and store in in local
    '''
    if not id_:
        id_ = __opts__['id']

    def _do_pass(id_):
        defaults_users = ['root', 'sysadmin']
        pw_reg = __salt__['mc_macros.get_local_registry'](
            'passwords_map', registry_format='pack')
        db_reg = __salt__['mc_pillar.query']('passwords_map')
        users, crypted, store= [], {}, False
        pw_id = pw_reg.setdefault(id_, {})
        db_id = db_reg.setdefault(id_, {})
        for users_list in [pw_id, db_id, defaults_users]:
            for user in users_list:
                if not user in users:
                    users.append(user)
        for user in users:
            pws = get_password(id_, user)
            pw = pws['clear']
            cpw = pws['crypted']
            crypted[user] = cpw
            pw_id[user] = pw
            db_id[user] = pw
        passwords = {'clear': pw_id, 'crypted': crypted}
        return passwords
    cache_key = 'mc_pillar.get_passwords_{0}'.format(id_)
    return memoize_cache(_do_pass, [id_], {}, cache_key, ttl)


def regenerate_passwords(ids_=None, users=None):
    pw_reg = __salt__['mc_macros.get_local_registry'](
        'passwords_map', registry_format='pack')
    if ids_ and not isinstance(ids_, list):
        ids_ = ids_.split(',')
    if users and not isinstance(users, list):
        users = users.split(',')
    for pw_id in [a for a in pw_reg]:
        data = pw_reg[a]
        if ids_ and pw_id not in ids_:
            continue
        for u, pw, in copy.deepcopy(data).items():
            print pw_id, u
            if users and u not in users:
                continue
            pw = get_password(pw_id, u, force=True)


def get_ssh_groups(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do_ssh_grp(id_, sysadmins=None):
        db_ssh_groups = __salt__['mc_pillar.query']('ssh_groups')
        ssh_groups = db_ssh_groups.get(
            id_,  db_ssh_groups['default'])
        for group in db_ssh_groups['default']:
            if group not in ssh_groups:
                ssh_groups.append(group)
        return ssh_groups
    cache_key = 'mc_pillar.get_ssh_groups_{0}'.format(id_)
    return memoize_cache(_do_ssh_grp, [id_], {}, cache_key, ttl)


def get_sudoers(id_=None, ttl=60):
    if not id_:
        id_ = __opts__['id']
    def _do_sudoers(id_, sysadmins=None):
        sudoers_map = __salt__['mc_pillar.query']('sudoers_map')
        sudoers = sudoers_map.get(id_, [])
        for s in sudoers_map['default']:
            if s not in (sudoers + ['infra']):
                sudoers.append(s)
        return sudoers
    cache_key = 'mc_pillar.get_sudoers_{0}'.format(id_)
    return memoize_cache(_do_sudoers, [id_], {}, cache_key, ttl)


def backup_default_configuration_type_for(id_, ttl=60):
    def _do(id_):
        db = get_db_infrastructure_maps()
        confs = query('backup_configuration_map')
        if id_ not in db['non_managed_hosts']:
            if id_ in db['vms']:
                id_ = 'default-vm'
            else:
                id_ = 'default'
        return confs.get(id_, None)
    cache_key = 'mc_pillar.backup_default_configuration_type_for{0}'.format(
        id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def backup_configuration_type_for(id_, ttl=60):
    def _do(id_):
        confs = query('backup_configuration_map')
        return confs.get(id_, None)
    cache_key = 'mc_pillar.backup_configuration_type_for{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def backup_configuration_for(id_, ttl=60):
    def _do(id_):
        db = get_db_infrastructure_maps()
        default_conf_id = __salt__[
            'mc_pillar.backup_default_configuration_type_for'](id_)
        confs = query('backup_configurations')
        conf_id = __salt__['mc_pillar.backup_configuration_type_for'](id_)
        data = OrderedDict()
        if id_ not in db['non_managed_hosts'] and not default_conf_id:
            raise ValueError(
                'No backup info for {0}'.format(id_))
        if id_ in db['non_managed_hosts'] and not conf_id:
            conf_id = __salt__['mc_pillar.backup_configuration_type_for'](
                'default')
            #raise ValueError(
            #    'No backup info for {0}'.format(id_))
        # load default conf
        default_conf = confs.get(default_conf_id, OrderedDict())
        conf = confs.get(conf_id, OrderedDict())
        for k in [a for a in default_conf if a.startswith('add_')]:
            adding = k.split('add_', 1)[1]
            ddata = data.setdefault(adding, [])
            ddata.extend([a for a in default_conf[k] if a not in ddata])
        data = __salt__['mc_utils.dictupdate'](data, default_conf)
        # load per host conf
        if conf_id != default_conf_id:
            for k in [a for a in conf if a.startswith('add_')]:
                adding = k.split('add_', 1)[1]
                ddata = data.setdefault(adding, [])
                ddata.extend([a for a in conf[k] if a not in ddata])
            data = __salt__['mc_utils.dictupdate'](data, conf)
        for cfg in [default_conf, conf]:
            for revove_key in ['remove', 'delete', 'del']:
                for k, val in [a
                               for a in cfg.items()
                               if a[0].startswith('remove_')]:
                    removing = k.split('{0}_'.format(remove_key),
                                       1)[1]
                    ddata = data.setdefault(removing, [])
                    for item in [obj for obj in ddata if obj in val]:
                        if item in ddata:
                            ddata.pop(ddata.index(item))
        return data
    cache_key = 'mc_pillar.backup_configuration_for{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def backup_server_for(id_, ttl=60):
    def _do(id_):
        confs = query('backup_server_map')
        return confs.get(id_, confs['default'])
    cache_key = 'mc_pillar.backup_server_for{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def backup_server(id_, ttl=60):
    def _do(id_):
        confs = query('backup_servers')
        return confs[id_]
    cache_key = 'mc_pillar.backup_server{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def is_burp_server(id_, ttl=60):
    def _do(id_):
        confs = query('backup_servers')
        return 'burp' in confs.get(id_, {}).get('types', [])
    cache_key = 'mc_pillar.is_burp_server{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def backup_server_settings_for(id_, ttl=60):
    def _do(id_):
        data = OrderedDict()
        db = get_db_infrastructure_maps()
        ndb = load_network_infrastructure()
        # pretendants are all managed baremetals excluding non managed
        # hosts and current backup server
        db['non_managed_hosts'] + [id_]
        gconf = get_configuration(id_)
        backup_excluded = ['default', 'default-vm']
        backup_excluded.extend(id_)
        manual_hosts = query('backup_manual_hosts')
        non_managed_hosts = query('non_managed_hosts')
        backup_excluded.extend([a for a in db['non_managed_hosts']
                                if a not  in manual_hosts])
        bms = [a for a in db['bms']
               if a not in backup_excluded
               and get_configuration(a)['manage_backups']]
        vms = [a for a in db['vms']
               if a not in backup_excluded
               and get_configuration(a)['manage_backups']]
        cmap = query('backup_configuration_map')
        manual_hosts = __salt__['mc_utils.uniquify']([
            a for a in ([a for a in cmap] + manual_hosts)
            if a not in backup_excluded
            and __salt__['mc_pillar.ip_for'](a)  # ip is resolvable via our pillar
            and a not in bms
            and a not in vms])
        # filter all baremetals and vms if they are tied to this backup
        # server
        server_conf = data.setdefault('server_conf',
                                      __salt__['mc_pillar.backup_server'](id_))
        confs = data.setdefault('confs', {})
        for host in bms + vms + manual_hosts:
            server = backup_server_for(host)
            if not server == id_:
                continue
            conf =__salt__['mc_pillar.backup_configuration_for'](host)
            # for vms, set the vm host as the gateway by default (if
            # not defined)
            if host in vms and host not in non_managed_hosts:
                conf.setdefault('ssh_gateway', db['vms'][host]['target'])
                conf.setdefault('ssh_gateway_port', '22')
            elif host in bms:
                pass

            type_ = conf.get('backup_type', server_conf['default_type'])
            confs[host] = {'type': type_, 'conf': conf}
        data['confs'] = confs
        return data
    cache_key = 'mc_pillar.backup_server_settings_for{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_top_variables(ttl=15):
    def _do_top():
        data = {}
        data.update(get_db_infrastructure_maps())
        return data
    cache_key = 'mc_pillar.get_top_variables'
    return memoize_cache(_do_top, [], {}, cache_key, ttl)


def is_dns_slave(id_, ttl=60):
    def _do(id_):
        if id_ in __salt__['mc_pillar.get_nss']()['slaves']:
            return True
        return False
    cache_key = 'mc_pillar.is_dns_slave_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def is_dns_master(id_, ttl=60):
    def _do(id_):
        if id_ in __salt__['mc_pillar.get_nss']()['masters']:
            return True
        return False
    cache_key = 'mc_pillar.is_dns_master_{0}'.format(id_)
    return memoize_cache(_do, [id_], {}, cache_key, ttl)


def get_makina_states_variables(id_, ttl=60):
    def _do_ms_var(id_):
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
    return memoize_cache(_do_ms_var, [id_], {}, cache_key, ttl)


def get_supervision_conf_kind(id_, kind):
    rdata = {}
    supervision = query('supervision_configurations')
    for cid, data in supervision.items():
        if data.get(kind, '') == id_:
            rdata.update(data.get('{0}_conf'.format(kind), {}))
            if 'nginx' in rdata:
                nginx = rdata['nginx']
                nginx = rdata.setdefault('nginx', {})
                domain = rdata.get('nginx', {}).get('domain', id_)
                cert, key = __salt__['mc_ssl.selfsigned_ssl_certs'](domain, True)[0]
                # unlonwn ca signed certs do not work in nginx
                # cert, key = __salt__['mc_ssl.ssl_certs'](domain, True)[0]
                # nginx['ssl_cacert'] = __salt__['mc_ssl.get_cacert'](True)
                nginx['ssl_key'] = key
                nginx['ssl_cert'] = cert
                nginx['ssl_redirect'] = True

    return rdata


def is_cloud_vm(target):
    ret = False
    maps = __salt__['mc_pillar.get_db_infrastructure_maps']()
    if target in maps['cloud_vms']:
        ret = True
    return ret


def is_cloud_compute_node(target):
    ret = False
    maps = __salt__['mc_pillar.get_db_infrastructure_maps']()
    if target in maps['cloud_compute_nodes']:
        ret = True
    return ret


def get_supervision_objects_defs(id_):
    rdata = {}
    net = load_network_infrastructure()
    disable_common_checks = {'disk_space': False,
                             'load_avg': False,
                             'memory': False,
                             'apt': False,
                             'swap': False,
                             'ping': False,
                             'nic_card': False}
    providers = __salt__['mc_network.providers']()
    if is_supervision_kind(id_, 'master'):
        data = query('supervision_configurations')
        defs = data.get('definitions', {})
        sobjs = defs.setdefault('objects', OrderedDict())
        hhosts = defs.setdefault('autoconfigured_hosts', OrderedDict())
        maps = __salt__['mc_pillar.get_db_infrastructure_maps']()
        for host, vts in maps['bms'].items():
            hdata = hhosts.setdefault(host, OrderedDict())
            attrs = hdata.setdefault('attrs', OrderedDict())
            groups = attrs.setdefault('groups', [])
            parents = attrs.setdefault('parents', [])
            tipaddr = attrs.setdefault('address', ip_for(host))
            attrs.setdefault('vars.SSH_PORT', 22)
            attrs.setdefault('vars.SNMP_PORT', 161)
            attrs.setdefault('vars.SSH_HOST', attrs['address'])
            attrs.setdefault('vars.SNMP_HOST', attrs['address'])
            if vts:
                hdata['memory_mode'] = 'large'
            for vt in ['lxc', 'kvm', 'xen', 'docker']:
                attrs['vars.{0}'.format(vt)] = vt in vts
                if vt in vts:
                    [groups.append(i)
                     for i in ['HG_HYPERVISOR',
                               'HG_HYPERVISOR_{0}'.format(vt)]
                     if i not in groups]
            # try to guess provider from name to avoid a whois lookup
            host_provider = None
            for provider in providers:
                if host.startswith(provider):
                    host_provider = provider
                    break
            if not host_provider:
                for provider in providers:
                    if __salt__['mc_network.is_{0}'.format(provider)]:
                        host_provider = provider
                        break
            if host_provider:
                [groups.append(i)
                 for i in ['HG_HOSTS',
                           'HG_PROVIDER',
                           'HG_PROVIDER_{0}'.format(host_provider)]
                 if i not in groups]
            if host not in maps['non_managed_hosts']:
                ds = hdata.setdefault('disk_space', [])
                for i in ['/', '/srv']:
                    if i not in ds:
                        ds.append(i)
        vm_parent = None
        if is_cloud_vm(id_):
            vm_parent = maps['vms'][id_]['target']
        for vm, vdata in maps['vms'].items():
            vt = vdata['vt']
            host = vdata['target']
            host_ip = ip_for(host)
            hdata = hhosts.setdefault(vm, OrderedDict())
            attrs = hdata.setdefault('attrs', OrderedDict())
            parents = attrs.setdefault('parents', [])
            tipaddr = attrs.setdefault('address', ip_for(vm))
            ssh_host = snmp_host = tipaddr
            snmp_port = 161
            ssh_port = 22
            if host not in parents:
                parents.append(host)
            # set the local ip for snmp and ssh
            if vm_parent == host:
                ssh_host = snmp_host = (
                    __salt__['mc_cloud_compute_node.find_ip_for_vm'](
                        host, vm, virt_type=vt))
            # we can access sshd and snpd on cloud vms
            # thx to special port mappings
            if is_cloud_vm(vm) and (vm_parent != host):
                ssh_port = (
                    __salt__['mc_cloud_compute_node.get_ssh_port'](
                        vm, host))
                snmp_port = (
                    __salt__['mc_cloud_compute_node.get_snmp_port'](
                        vm, host))
            no_common_checks = False
            if tipaddr == host_ip:
                no_common_checks = True
            groups = attrs.setdefault('groups', [])
            [groups.append(i)
             for i in ['HG_HOSTS', 'HG_VMS', 'HG_VM_{0}'.format(vt)]
             if i not in groups]
            # those checks are useless on lxc
            if vt in ['lxc'] and vm in maps['non_managed_hosts']:
                no_common_checks = True
            if no_common_checks:
                hdata.update(disable_common_checks)
            attrs['vars.SSH_HOST'] = ssh_host
            attrs['vars.SNMP_HOST'] = snmp_host
            attrs['vars.SSH_PORT'] = ssh_port
            attrs['vars.SNMP_PORT'] = snmp_port
        for host, hdata in hhosts.items():
            parents = hdata.setdefault('attrs', {}).setdefault('parents', [])
            rparents = [a for a in parents if a != id_]
            groups = hdata.get('attrs', {}).get('groups', [])
            for g in groups:
                if g not in sobjs:
                    sobjs[g] = {'attrs': {'display_name': g}}
            # if we defined parents but no address, we should rely on an
            # dns query to get the ip fromand cross it over the failover map
            # as the goal is to resolve any mounted failover ip as the
            # address of this supervised entry
            if (
                'address' not in hdata['attrs']
                and rparents
            ):
                socket.setdefaulttimeout(1)
                addr = socket.gethostbyname(host)
                failover = [a for a in parents if a in net['ipsfo_map']]
                for h in failover:
                    if addr in ips_for(h, fail_over=True):
                        hdata['attrs']['address'] = addr
                        hdata.update(disable_common_checks)
                        break
            if id_ not in parents:
                parents.append(id_)
            if not hdata['attrs'].get('address'):
                raise ValueError('no address defined for {0}'.format(host))
        rdata.update({'icinga2_definitions': defs})
    return rdata


def get_supervision_pnp_conf(id_, ttl=60):
    def _do_ms_var(id_):
        k = 'makina-states.services.monitoring.pnp4nagios'
        return {k: get_supervision_conf_kind(id_, 'pnp')}
    cache_key = 'mc_pillar.get_supervision_pnp_conf{0}'.format(id_)
    return memoize_cache(_do_ms_var, [id_], {}, cache_key, ttl)


def get_supervision_nagvis_conf(id_, ttl=60):
    def _do_ms_var(id_):
        k = 'makina-states.services.monitoring.nagvis'
        return {k: get_supervision_conf_kind(id_, 'nagvis')}
    cache_key = 'mc_pillar.get_supervision_nagvis_conf{0}'.format(id_)
    return memoize_cache(_do_ms_var, [id_], {}, cache_key, ttl)


def get_supervision_ui_conf(id_, ttl=60):
    def _do_ms_var(id_):
        k = 'makina-states.services.monitoring.icinga_web'
        return {k: get_supervision_conf_kind(id_, 'ui')}
    cache_key = 'mc_pillar.get_supervision_ui_conf{0}'.format(id_)
    return memoize_cache(_do_ms_var, [id_], {}, cache_key, ttl)


def is_supervision_kind(id_, kind, ttl=60):
    def _do_ms_var(id_, kind):
        supervision = query('supervision_configurations')
        if not supervision:
            return False
        for cid, data in supervision.items():
            if data.get(kind, '') == id_:
                return True
        return False
    cache_key = 'mc_pillar.is_supervision_master{0}{1}'.format(id_,
                                                               kind)
    return memoize_cache(_do_ms_var, [id_, kind], {}, cache_key, ttl)


def format_rrs(domain, alt=None):
    infos = __salt__['mc_pillar.get_nss_for_zone'](domain)
    master = infos['master']
    slaves = infos['slaves']
    allow_transfer = []
    if slaves:
        slaveips = []
        for s in slaves:
            slaveips.append('key "{0}"'.format(
                __salt__['mc_pillar.ip_for'](s)))
        allow_transfer = slaveips
        soans = slaves.keys()[0]
    else:
        soans = master

    soans += "."
    if not alt:
        alt = domain
    rrs = [a.strip().replace(domain, alt)
           for a in __salt__['mc_pillar.rrs_for'](domain, aslist=True)
           if a.strip()]
    rdata = {
        'allow_transfer': allow_transfer,
        'serial': __salt__['mc_pillar.serial_for'](domain),
        'soa_ns': soans.replace(domain, alt),
        'soa_contact': 'postmaster.{0}.'.format(domain).replace(
            domain, alt),
        'rrs': rrs}
    return rdata


def slave_key(id_, dnsmaster=None, master=True):
    ip_for = __salt__['mc_pillar.ip_for']
    rdata = {}
    oip = ip_for(id_)
    if not master:
        mip = ip_for(dnsmaster)
        # on slave side, declare the master as the tsig
        # key consumer
        rdata[
            'makina-states.services.dns.bind.servers.{0}'.format(
                mip)] = {'keys': [oip]}
    # on both, say to encode with the client tsig key when daemons
    # are talking to each other
    rdata['makina-states.services.dns.bind.keys.{0}'.format(oip)] = {
        'secret': __salt__['mc_bind.tsig_for'](oip)}
    return rdata


def get_dns_slave_conf(id_):
    if not __salt__['mc_pillar.is_dns_slave'](id_):
        return {}
    rdata = {
        'makina-states.services.dns.bind': True
    }
    dnsmasters = {}
    domains = __salt__[
        'mc_pillar.get_slaves_zones_for'](id_)
    for domain, masterdn in domains.items():
        master = __salt__['mc_pillar.ip_for'](
            masterdn)
        if masterdn not in dnsmasters:
            dnsmasters.update({masterdn: master})
        rdata['makina-states.services.dns.bind'
              '.zones.{0}'.format(domain)] = {
                  'server_type': 'slave',
                  'masters': [master]}
    for dnsmaster, masterip in dnsmasters.items():
        rdata.update(
            slave_key(id_, dnsmaster, master=False))
    return rdata


def get_dns_master_conf(id_):
    if not __salt__['mc_pillar.is_dns_master'](id_):
        return {}
    rdata = {
        'makina-states.services.dns.bind': True
    }
    altdomains = []
    for domains in __salt__['mc_pillar.query'](
        'managed_alias_zones'
    ).values():
        altdomains.extend(domains)
    for domain in __salt__[
        'mc_pillar.query'](
            'managed_dns_zones'):
        if domain not in altdomains:
            rdata[
                'makina-states.services.dns.bind'
                '.zones.{0}'.format(domain)] = __salt__[
                    'mc_pillar.format_rrs'](domain)
    for domain, altdomains in __salt__[
        'mc_pillar.query'](
            'managed_alias_zones').items():
        for altdomain in altdomains:
            srrs = __salt__['mc_pillar.format_rrs'](
                domain, alt=altdomain)
            rdata['makina-states.services.dns.bind'
                  '.zones.{0}'.format(altdomain)] = srrs
    dnsslaves = __salt__[
        'mc_pillar.get_slaves_for'](id_)['all']
    if dnsslaves:
        # slave tsig declaration
        rdata[
            'makina-states.services.dns.bind.slaves'
        ] = [__salt__['mc_pillar.ip_for'](slv)
             for slv in dnsslaves]
        for dn in dnsslaves:
            rdata.update(slave_key(dn))
            rdata[
                'makina-states.services.dns.bind'
                '.servers.{0}'.format(
                    __salt__['mc_pillar.ip_for'](dn)
                )
            ] = {
                'keys': [
                    __salt__['mc_pillar.ip_for'](dn)]
            }
    return rdata


def manage_network_common(fqdn):
    rdata = {
        'makina-states.localsettings.network.managed': True,
        'makina-states.localsettings.hostname': fqdn.split('.')[0]
    }
    return rdata


def manage_bridged_fo_kvm_network(fqdn, host, ipsfo,
                                  ipsfo_map, ips,
                                  thisip=None,
                                  ifc='eth0'):
    ''''
    setup the network adapters configuration
    for a kvm vm on an ip failover setup'''
    rdata = {}
    if not thisip:
        thisip = ipsfo[ipsfo_map[fqdn][0]]
    gw = __salt__['mc_network.get_gateway'](
        host, ips[host][0])
    rdata.update(manage_network_common(fqdn))
    rdata['makina-states.localsettings.network.ointerfaces'] = [{
        ifc: {
            'address': thisip,
            'netmask': __salt__[
                'mc_network.get_fo_netmask'](fqdn, thisip),
            'broadcast': __salt__[
                'mc_network.get_fo_broadcast'](fqdn, thisip),
            'dnsservers': __salt__[
                'mc_network.get_dnss'](fqdn, thisip),
            'post-up': [
                'route add {0} dev {1}'.format(gw, ifc),
                'route add default gw {0}'.format(gw),
            ]
        }
    }]


def manage_baremetal_network(fqdn, ipsfo, ipsfo_map,
                             ips, thisip=None,
                             thisipfos=None, ifc='',
                             out_nic='eth0'):
    rdata = {}
    if not thisip:
        thisip = ips[fqdn][0]
    if not thisipfos:
        thisipfos = []
        thisipifosdn = ipsfo_map.get(fqdn, [])
        for dns in thisipifosdn:
            thisipfos.append(ipsfo[dns])
    rdata.update(manage_network_common(fqdn))
    # br0: we use br0 as main interface with by
    # defaultonly one port to escape to internet
    if 'br' in ifc:
        net = rdata[
            'makina-states.localsettings.network.'
            'ointerfaces'
        ] = [{
            ifc: {
                'address': thisip,
                'bridge_ports': out_nic,
                'broadcast': __salt__[
                    'mc_network.get_broadcast'](fqdn, thisip),
                'netmask': __salt__[
                    'mc_network.get_netmask'](fqdn, thisip),
                'gateway': __salt__[
                    'mc_network.get_gateway'](fqdn, thisip),
                'dnsservers': __salt__[
                    'mc_network.get_dnss'](fqdn, thisip)
            }},
            {out_nic: {'mode': 'manual'}},
        ]
    # eth0/em0: do not use bridge but a
    # real interface
    else:
        ifc = out_nic
        net = rdata[
            'makina-states.localsettings.network.'
            'ointerfaces'
        ] = [{
            ifc: {
                'address': thisip,
                'broadcast': __salt__[
                    'mc_network.get_broadcast'](fqdn, thisip),
                'netmask': __salt__[
                    'mc_network.get_netmask'](fqdn, thisip),
                'gateway': __salt__[
                    'mc_network.get_gateway'](fqdn, thisip),
                'dnsservers': __salt__[
                    'mc_network.get_dnss'](fqdn, thisip)
            }
        }]
    if thisipfos:
        for ix, thisipfo in enumerate(thisipfos):
            ifinfo = {"{0}_{1}".format(ifc, ix): {
                'ifname': "{0}:{1}".format(ifc, ix),
                'address': thisipfo,
                'netmask': __salt__[
                    'mc_network.get_fo_netmask'](fqdn, thisipfo),
                'broadcast': __salt__[
                    'mc_network.get_fo_broadcast'](fqdn, thisipfo),
            }}
            net.append(ifinfo)
    return rdata


def get_sysnet_conf(id_):
    gconf = get_configuration(id_)
    ms_vars = get_makina_states_variables(id_)
    rdata = {}
    net = __salt__['mc_pillar.load_network_infrastructure']()
    ips = net['ips']
    ipsfo = net['ipsfo']
    ipsfo_map = net['ipsfo_map']
    if not (
        ms_vars.get('is_bm', False)
        and gconf.get('manage_network', False)
    ):
        return {}
    if id_ in net['non_managed_hosts']:
        return {}
    if id_ in net['baremetal_hosts']:
        # always use bridge as main_if
        rdata.update(
            manage_baremetal_network(
                id_, ipsfo, ipsfo_map, ips, ifc='br0'))
    else:
        for vt, targets in net['vms'].items():
            if vt != 'kvm':
                continue
            for target, vms in targets.items():
                if id_ not in vms:
                    continue
                manage_bridged_fo_kvm_network(
                    id_, target, ipsfo,
                    ipsfo_map, ips)
    return rdata


def get_snmpd_conf(id_):
    data = __salt__['mc_pillar.get_snmpd_settings'](id_)
    gconf = get_configuration(id_)
    rdata = {}
    pref = "makina-states.services.monitoring.snmpd"
    if gconf.get('manage_snmpd', False):
        rdata.update({
            pref: True,
            pref + ".default_user": data['user'],
            pref + ".default_password": data['password'],
            pref + ".default_key": data['key']})
    return rdata


def get_backup_client_conf(id_):
    gconf = get_configuration(id_)
    rdata = {}
    if gconf.get('manage_backups', False):
        conf = __salt__['mc_pillar.get_configuration'](id_)
        mode = conf['backup_mode']
        if mode == 'rdiff':
            rdata['makina-states.services.backup.rdiff-backup'] = True
        elif 'burp' in mode:
            rdata['makina-states.services.backup.burp.client'] = True
    return rdata


def get_supervision_master_conf(id_, ttl=60):
    def _do_ms_var(id_):
        rdata = {}
        k = 'makina-states.services.monitoring.icinga2'
        rdata[k] = get_supervision_conf_kind(id_, 'master')
        rdata['makina-states.services.monitoring.'
              'icinga2.modules.cgi.enabled'] = False
        return rdata
    cache_key = 'mc_pillar.get_supervision_master_conf{0}'.format(id_)
    return memoize_cache(_do_ms_var, [id_], {}, cache_key, ttl)


def get_supervision_confs(id_):
    rdata = {}
    for kind in ['master', 'ui', 'pnp', 'nagvis']:
        if __salt__['mc_pillar.is_supervision_kind'](id_, kind):
            rdata.update({
                'master': get_supervision_master_conf,
                'ui': get_supervision_ui_conf,
                'pnp': get_supervision_pnp_conf,
                'nagvis': get_supervision_nagvis_conf
            }[kind](id_))
    rdata.update(
        __salt__['mc_pillar.get_supervision_objects_defs'](id_))
    return rdata


def get_sudoers_conf(id_):
    gconf = get_configuration(id_)
    rdata = {}
    pref = "makina-states.localsettings.admin.sudoers"
    if gconf.get('manage_sudoers', False):
        rdata.update({
            pref: __salt__['mc_pillar.get_sudoers'](id_)})
    return rdata


def get_packages_conf(id_):
    gconf = get_configuration(id_)
    rdata = {}
    pref = "makina-states.localsettings.pkgs.apt"
    if gconf.get('manage_packages', False):
        rdata.update({
            pref + ".ubuntu.mirror": "http://mirror.ovh.net/ftp.ubuntu.com/",
            pref + ".debian.mirror": (
                "http://mirror.ovh.net/ftp.debian.org/debian/")
        })
    return rdata


def get_default_env_conf(id_):
    conf = get_configuration(id_)
    rdata = {}
    conf = __salt__['mc_pillar.get_configuration'](id_)
    rdata['default_env'] = conf['default_env']
    return rdata


def get_shorewall_conf(id_):
    gconf = get_configuration(id_)
    rdata = {}
    if gconf.get('manage_shorewall', False):
        rdata.update(__salt__['mc_pillar.get_shorewall_settings'](id_))
    return rdata


def get_autoupgrade_conf(id_):
    ms_vars = get_makina_states_variables(id_)
    gconf = get_configuration(id_)
    rdata = {}
    if ms_vars.get('is_bm', False):
        rdata['makina-states.localsettings.autoupgrade'] = gconf[
            'manage_autoupgrades']
    return rdata


def get_fail2ban_conf(id_):
    gconf = get_configuration(id_)
    rdata = {}
    pref = "makina-states.services.firewall.fail2ban"
    if gconf.get('manage_snmpd', False):
        rdata.update({
            pref: True,
            pref + ".ignoreip": __salt__['mc_pillar.whitelisted'](id_)})
    return rdata


def get_ntp_server_conf(id_):
    gconf = get_configuration(id_)
    rdata = {}
    if gconf.get('manage_ntp_server', False):
        rdata.update({
            'makina-states.services.base.ntp.kod': False,
            'makina-states.services.base.ntp.peer': False,
            'makina-states.services.base.ntp.trap': False,
            'makina-states.services.base.ntp.query': False})
    return rdata


def get_ldap_client_conf(id_):
    gconf = get_configuration(id_)
    rdata = {}
    if gconf.get('ldap_client', False):
        conf = __salt__['mc_pillar.get_ldap_configuration'](id_)
        rdata['makina-states.localsettings.ldap'] = {
            'ldap_uri': conf['ldap_uri'],
            'ldap_base': conf['ldap_base'],
            'ldap_passwd': conf['ldap_passwd'],
            'ldap_shadow': conf['ldap_shadow'],
            'ldap_group': conf['ldap_group'],
            'ldap_cacert': conf['ldap_cacert'],
            'enabled': conf['enabled'],
            'nslcd': {'ssl': conf['nslcd']['ssl']}}
    return rdata


def get_mail_conf(id_):
    gconf = get_configuration(id_)
    if not gconf.get('manage_mails', False):
        return {}
    data = {}
    mail_conf = __salt__['mc_pillar.get_mail_configuration'](id_)
    dest = mail_conf['default_dest'].format(id=id_)
    data['makina-states.services.mail.postfix'] = True
    data['makina-states.services.mail.postfix.mode'] = mail_conf['mode']
    if mail_conf.get('transports'):
        transports = data.setdefault(
            'makina-states.services.mail.postfix.transport', [])
        for entry, host in mail_conf['transports'].items():
            if entry != '*':
                transports.append({
                    'transport': entry,
                    'nexthop': 'relay:[{0}]'.format(host)})
        if '*' in mail_conf['transports']:
            transports.append(
                {'nexthop':
                 'relay:[{0}]'.format(mail_conf['transports']['*'])})
        if mail_conf['auth']:
            passwds = data.setdefault(
                'makina-states.services.mail.postfix.sasl_passwd', [])
            data['makina-states.services.mail.postfix.auth'] = True
            for entry, host in mail_conf['smtp_auth'].items():
                passwds.append({
                    'entry': '[{0}]'.format(entry),
                    'user': host['user'],
                    'password': host['password']})
        if mail_conf.get('virtual_map'):
            vmap = data.setdefault(
                'makina-states.services.mail.postfix.virtual_map', {})
        for record in mail_conf['virtual_map']:
            for item, val in record.items():
                vmap[item.format(id=id_, dest=dest)] = val.format(
                    id=id_, dest=dest)
    return data


def get_ssh_keys_conf(id_):
    gconf = get_configuration(id_)
    rdata = {}
    pref = "makina-states.services.base.ssh.server"
    adm_pref = "makina-states.localsettings.admin.sysadmins_keys"
    a_adm_pref = "makina-states.localsettings.admin.absent_keys"
    if gconf.get('manage_ssh_keys', False):
        absent_keys = []
        for k in __salt__['mc_pillar.get_removed_keys'](id_):
            absent_keys.append({k: {}})
        rdata.update({
            adm_pref: __salt__['mc_pillar.get_sysadmins_keys'](id_),
            a_adm_pref: absent_keys,
            pref + ".chroot_sftp": True})
    return rdata


def get_ssh_groups_conf(id_):
    gconf = get_configuration(id_)
    rdata = {}
    pref = "makina-states.services.base.ssh.server"
    if gconf.get('manage_ssh_groups', False):
        rdata.update({
            pref + ".allowgroups": __salt__['mc_pillar.get_ssh_groups'](id_),
            pref + ".chroot_sftp": True})
    return rdata


def get_etc_hosts_conf(id_):
    gconf = get_configuration(id_)
    rdata = {}
    if gconf.get('manage_hosts', False):
        hosts = __salt__['mc_pillar.query']('hosts').get(id_, [])
        if hosts:
            dhosts = rdata.setdefault('makina-bosts', [])
            for entry in hosts:
                ip = entry.get('ip', __salt__['mc_pillar.ip_for'](id_))
                dhosts.append({'ip': ip, 'hosts': entry['hosts']})
    return rdata


def get_passwords_conf(id_):
    '''
    Idea is to have
    - simple users gaining sudoer access
    - powerusers known as sysadmin have:
        - access to sysadmin user via ssh key
        - access to root user via ssh key
    - They are also sudoers with their username (trigramme)
    - ssh accesses are limited though access groups, so we also map here
      the groups which have access to specific machines
    '''
    gconf = get_configuration(id_)
    ms_vars = get_makina_states_variables(id_)
    rdata = {}
    pref = "makina-states.localsettings"
    apref = pref + ".admin"
    if gconf.get('manage_passwords', False):
        passwords = __salt__['mc_pillar.get_passwords'](id_)
        for user, password in passwords['crypted'].items():
            if user not in ['root', 'sysadmin']:
                rdata[
                    pref + '.users.{0}.password'.format(
                        user)] = password
        rdata.update({
            apref + ".root_password": passwords['crypted']['root'],
            apref + ".sysadmin_password": passwords['crypted']['sysadmin']})
    return rdata


def get_cloud_image_conf(id_):
    rdata = {}
    gconf = get_configuration(id_)
    if gconf.get('cloud_images'):
        rdata.update(gconf['cloud_images'])
    return rdata


def get_cloudmaster_conf(id_):
    gconf = get_configuration(id_)
    ms_vars = get_makina_states_variables(id_)
    if not gconf.get('cloud_master', False):
        return {}
    gconf = get_configuration(id_)
    pref = 'makina-states.cloud'
    rdata = {
        pref + '.generic': True,
        pref + '.master': gconf['mastersaltdn'],
        pref + '.master_port': gconf['mastersalt_port'],
        pref + '.saltify': True,
        pref + '.lxc': True,
        pref + '.lxc.defaults.backing': 'dir'
    }
    for i in [get_cloud_image_conf,
              get_cloud_vm_conf,
              get_cloud_compute_node_conf]:
        rdata.update(i(id_))
    return rdata


def get_cloud_vm_conf(id_):
    rdata = {}
    cloud_vm_attrs = __salt__['mc_pillar.query']('cloud_vm_attrs')
    nvars  = __salt__['mc_pillar.load_network_infrastructure']()
    supported_vts = ['lxc']
    for vt, targets in nvars['vms'].items():
        if vt not in supported_vts:
            continue
        for compute_node, vms in targets.items():
            if compute_node in nvars['non_managed_hosts']:
                continue
            k = ('makina-states.cloud.lxc.'
                 'vms.{0}').format(compute_node)
            pvms = rdata.setdefault(k, {})
            for vm in vms:
                if vm in nvars['non_managed_hosts']:
                    continue
                dvm = pvms.setdefault(vm, {})
                metadata = cloud_vm_attrs.get(vm, {})
                metadata.setdefault('profile_type',
                                    'dir')
                if 'password' not in metadata:
                    metadata.setdefault(
                        'password',
                        __salt__[
                            'mc_pillar.get_passwords'
                        ](vm)['clear']['root'])
                dvm.update(metadata)
    return rdata


def get_cloud_compute_node_conf(id_):
    rdata = {}
    ms_vars = get_makina_states_variables(id_)
    # detect computes nodes by searching for related vms configurations
    supported_vts = ['lxc']
    done_hosts = []
    nvars  = __salt__['mc_pillar.load_network_infrastructure']()
    cloud_cn_attrs = nvars['cloud_cn_attrs']
    for vt, targets in nvars['vms'].items():
        if vt not in supported_vts:
            continue
        for compute_node, vms in targets.items():
            if not (
                (compute_node not in done_hosts)
                and
                (compute_node not in ms_vars['non_managed_hosts'])
            ):
                done_hosts.append(compute_node)
                rdata['makina-states.cloud.saltify'
                      '.targets.{0}'.format(
                          compute_node)] = {
                    'password': __salt__[
                        'mc_pillar.get_passwords'](
                            compute_node
                        )['clear']['root'],
                    'ssh_username': 'root'
                }
            metadata = cloud_cn_attrs.get(compute_node, {})

            haproxy_pre = metadata.get('haproxy', {}).get('raw_opts_pre', [])
            haproxy_post = metadata.get('haproxy', {}).get('raw_opts_post', [])
            for suf, opts in [
                a for a in [
                    ['pre,', haproxy_pre],
                    ['post', haproxy_post]
                ] if a[1]
            ]:
                rdata[
                    'makina-states.cloud.compute_node.conf.'
                    '{0}.http_proxy.raw_opts_{1}'.format(
                        compute_node, suf)] = opts

    for vt, targets in nvars['vms'].items():
        if vt not in supported_vts:
            continue
        for compute_node, vms in targets.items():
            if not (
                compute_node not in done_hosts
                and
                compute_node not in nvars['non_managed_hosts']
            ):
                continue
            done_hosts.append(compute_node)
            k = ('makina-states.cloud.'
                 'saltify.targets.{0}').format(
                     compute_node)
            rdata[k] = {
                'password': __salt__[
                    'mc_pillar.get_passwords'](
                        compute_node)['clear']['root'],
                'ssh_username': 'root'
            }

        for host, data in nvars['standalone_hosts'].items():
            if host in done_hosts:
                continue
            done_hosts.append(compute_node)
            sk = ('makina-states.cloud.saltify.'
                  'targets.{0}').format(host)
            rdata[sk] = {
                'ssh_username': data.get(
                    'ssh_username', 'root')
            }
            for k, val in data.items():
                if val and val not in ['ssh_username']:
                    rdata[sk][k] = val
    return rdata


def get_burp_server_conf(id_):
    rdata = {}
    if __salt__['mc_pillar.is_burp_server'](id_):
        conf = __salt__['mc_pillar.backup_server_settings_for'](id_)
        rdata['makina-states.services.backup.burp.server'] = True
        for host, conf in conf['confs'].items():
            if conf['type'] in ['burp']:
                rdata[
                    'makina-states.services.'
                    'backup.burp.clients.{0}'.format(host)
                ] = conf['conf']
    return rdata


def get_dhcpd_conf(id_):
    try:
        conf = query('dhcpd_conf')[id_]
    except KeyError:
        conf = {}
    if not conf:
        return {}
    return {
        'makina-states.services.dns.dhcpd': conf
    }


def get_slapd_pillar_conf(id_):
    rdata = {}
    if (
        __salt__['mc_pillar.is_ldap_master'](id_)
        or __salt__['mc_pillar.is_ldap_slave'](id_)
    ):
        data = __salt__['mc_pillar.get_slapd_conf'](id_)
        rdata['makina-states.services.dns.slapd'] = True
        for k in ['tls_cacert', 'tls_cert', 'tls_key',
                  'mode', 'config_pw', 'root_dn', 'dn', 'root_pw']:
            val = data.get(k, None)
            if val:
                rdata[
                    'makina-states.services.dns.slapd.{0}'.format(val)
                ] = val
    return rdata

# vim:set et sts=4 ts=4 tw=80:
