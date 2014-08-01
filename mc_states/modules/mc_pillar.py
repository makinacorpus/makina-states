#!/usr/bin/env python
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'
import json
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
                    if not fqdn in allslaves['all']:
                        allslaves['all'].append(fqdn)
                    if not fqdn in slaves:
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
            if ',all' in  restrict[param]:
                restrict[param] = 'all'
            if restrict[param] == 'net:all':
                restrict[param] = 'all'
        shw_params = {
          'makina-states.services.firewall.shorewall': True,
          'makina-states.services.firewall.shorewall.no_snmp': False,
          'makina-states.services.firewall.shorewall.no_ldap': False,
        }
        p_param = 'makina-states.services.firewall.shorewall.params.RESTRICTED_{0}'
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
    return rdata


def get_supervision_pnp_conf(id_, ttl=60):
    def _do_ms_var(id_):
        return get_supervision_conf_kind(id_, 'pnp')
    cache_key = 'mc_pillar.get_supervision_pnp_conf{0}'.format(id_)
    return memoize_cache(_do_ms_var, [id_], {}, cache_key, ttl)


def get_supervision_nagvis_conf(id_, ttl=60):
    def _do_ms_var(id_):
        return get_supervision_conf_kind(id_, 'nagvis')
    cache_key = 'mc_pillar.get_supervision_nagvis_conf{0}'.format(id_)
    return memoize_cache(_do_ms_var, [id_], {}, cache_key, ttl)


def get_supervision_ui_conf(id_, ttl=60):
    def _do_ms_var(id_):
        return get_supervision_conf_kind(id_, 'ui')
    cache_key = 'mc_pillar.get_supervision_ui_conf{0}'.format(id_)
    return memoize_cache(_do_ms_var, [id_], {}, cache_key, ttl)


def get_supervision_master_conf(id_, ttl=60):
    def _do_ms_var(id_):
        return get_supervision_conf_kind(id_, 'master')
    cache_key = 'mc_pillar.get_supervision_master_conf{0}'.format(id_)
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

# vim:set et sts=4 ts=4 tw=80:
