#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

'''

.. _module_mc_pillar:

mc_pillar / makinastates ext-pillar
===============================================

Transform the informations contained in database.sls to a whole infrastructure
mapping.


'''

import re
import inspect
import os
import cProfile
import json
import pstats
import copy
import hashlib
# Import python libs
import dns
import dns.query
import dns.resolver
import dns.message
import dns.rdatatype
import socket
import logging
import time
import mc_states.api
from mc_states import saltapi
import datetime
from salt.utils.pycrypto import secure_password
from salt.utils.odict import OrderedDict
import traceback
from mc_states.saltapi import (
    IPRetrievalError, RRError, NoResultError, PillarError)
six = mc_states.api.six

socket_errors = (
    socket.timeout,
    socket.error,
    socket.herror,
    socket.gaierror
)


rei_flags = re.M | re.U | re.S | re.I
log = logging.getLogger(__name__)
DOMAIN_PATTERN = '(@{0})|({0}\\.?)$'
DOTTED_DOMAIN_PATTERN = '(^{domain}|@{domain}|\\.{domain})\\.?$'
__name = 'mc_pillar'
_marker = object()
_cache = mc_states.api._LOCAL_CACHES.setdefault('mc_pillar', {})

SUPPORTED_DB_FORMATS = ['sls', 'yaml', 'json']
FIVE_MINUTES = mc_states.api.FIVE_MINUTES
TEN_MINUTES = mc_states.api.TEN_MINUTES
ONE_MINUTE = mc_states.api.ONE_MINUTE
HALF_HOUR = mc_states.api.HALF_HOUR
ONE_HOUR = mc_states.api.ONE_HOUR
ONE_DAY = mc_states.api.ONE_DAY
HALF_DAY = mc_states.api.HALF_DAY
ONE_MONTH = mc_states.api.ONE_MONTH
ONE_YEAR = ONE_MONTH * 12
FIREWALLD_MANAGED = False
MS_IPTABLES_MANAGED = True
CACHE_INC_TOKEN = '1116'

# pillar cache is never expired, only if we detect a change on the database file
PILLAR_TTL = ONE_YEAR


def minion_id():
    return __salt__['mc_utils.local_minion_id']()


def mmid():
    '''
    Alias
    '''
    return minion_id()


def yaml_load(*args, **kw3):
    return __salt__['mc_utils.cyaml_load'](*args, **kw3)


def yaml_dump(*args, **kw4):
    return __salt__['mc_utils.cyaml_dump'](*args, **kw4)


def generate_password(length=None):
    return __salt__['mc_utils.generate_password'](length)


def dolog(msg):
    log.error("----------------")
    log.error(msg)
    log.error("----------------")


class IPRetrievalCycleError(IPRetrievalError):
    ''''''


class DatabaseNotFound(KeyError):
    '''.'''


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


def get_db():
    dbpath = None
    base = os.path.join(
        os.path.dirname(os.path.abspath(__opts__['config_dir'])),
        'makina-states')
    for i in SUPPORTED_DB_FORMATS:
        dbpath = os.path.join( base, 'database.{0}'.format(i))
        if os.path.exists(dbpath):
            break
    return dbpath


def has_db():
    db = get_db()
    if (
        os.path.splitext(db)[1][1:] in SUPPORTED_DB_FORMATS
    ):
        return os.path.exists(db)
    else:
        return False

# to be easily mockable in tests while having it cached
def loaddb_do(*a, **kw5):
    dbpath = get_db()
    suf = os.path.splitext(dbpath)[1]
    suf = suf[1:]
    if suf not in SUPPORTED_DB_FORMATS:
        raise ValueError(
            'invalid db format {0}: {1}'.format(suf, dbpath))
    if not has_db():
        raise DatabaseNotFound("{0} is not present".format(dbpath))
    with open(get_db()) as fic:
        content = dbpath
        if suf not in ['sls']:
            content = fic.read()
        db = __salt__['mc_utils.{0}_load'.format(suf)](content)
    for item in db:
        types = (dict, list)
        if item in ['format']:
            types = (int,)
        if not isinstance(db[item], types):
            raise ValueError('Db is invalid for {0}'.format(item))
    return db


def load_db(ttl=PILLAR_TTL):
    cache_key = __name + '.load_db' + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        __salt__[__name + '.loaddb_do'],
        [], {}, cache=_cache, key=cache_key, seconds=ttl)


def query(doc_types, default=_marker, ttl=PILLAR_TTL, **kwargs):
    def _do(doc_types):
        try:
            db = __salt__[__name + '.load_db']()
            try:
                docs = db[doc_types]
            except (IndexError, KeyError):
                raise NoResultError('no {0} in database'.format(doc_types))
        except (NoResultError,) as exc:
            if default is not _marker:
                docs = default
            else:
                raise exc
        return docs
    cache_key = __name + '.query{0}'.format(doc_types) + CACHE_INC_TOKEN
    if default is _marker:
        cache_key += '_default'
    return __salt__['mc_utils.memoize_cache'](
        _do, [doc_types], kwargs, cache=_cache, key=cache_key, seconds=ttl)


def load_network(ttl=PILLAR_TTL, debug=None):
    def _do():
        __salt__[__name + '.load_db']()
        data = {'extra_info_loading': None,
                'raw_db_loading': None,
                'raw_db_loaded': False,
                'extra_info_loaded': False}
        for i in ['cnames', 'ips', 'ipsfo', 'ips_map', 'ipsfo_map']:
            data[i] = copy.deepcopy(__salt__[__name + '.query'](i, {}))
        return data
    # no memcached, relies on memoize !
    cache_key = __name + '._load_network' + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [], {}, cache=_cache, key=cache_key, seconds=ttl, debug=debug)


def _load_network(*a, **kw):
    '''
    retro compat wrapper
    '''
    return load_network(**kw)


def get_global_clouf_conf(entry, ttl=PILLAR_TTL):
    def _do(entry):
        return get_global_conf('cloud_settings', entry)
    cache_key = __name + '.get_global_cloudconf{0}'.format(entry) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [entry], {}, cache_key, ttl)


def get_cloud_conf(ttl=PILLAR_TTL):
    def _do():
        rdata = OrderedDict()
        dvms = rdata.setdefault('vms', OrderedDict())
        dcns = rdata.setdefault('cns', OrderedDict())
        _s = __salt__
        # warm datastructs
        _s['mc_cloud.extpillar_settings']()
        nmh = _s[__name + '.query']('non_managed_hosts', {})
        cloud_cn_attrs = _s[__name + '.query']('cloud_cn_attrs', {})
        cloud_vm_attrs = _s[__name + '.query']('cloud_vm_attrs', {})
        supported_vts = _s['mc_cloud_compute_node.get_vts']()
        for vt, targets in _s[__name + '.query']('vms', {}).items():
            if vt not in supported_vts:
                continue
            for cn, vms in targets.items():
                if vms is None:
                    vms = {}
                if cn in nmh:
                    continue
                dcn = dcns.setdefault(cn, OrderedDict())
                dcns[cn] = dcn
                dcn.setdefault('conf', cloud_cn_attrs.get(cn, OrderedDict()))
                cn_vms = dcn.setdefault('vms', OrderedDict())
                vts = dcn.setdefault('vts', [])
                if vt not in vts:
                    vts.append(vt)
                for vm in vms:
                    if vm in nmh:
                        continue
                    vmdata = dvms.setdefault(vm, OrderedDict())
                    cvmdata = cloud_vm_attrs.get(vm, OrderedDict())
                    vmdata = _s['mc_utils.dictupdate'](vmdata, cvmdata)
                    vmdata['vt'] = vt
                    vmdata['target'] = cn
                    dvms[vm] = cn_vms[vm] = vmdata

        for cn in _s[__name + '.query']('baremetal_hosts'):
            if cn in nmh:
                continue
            dcn = dcns.setdefault(cn, OrderedDict())
            dcn.setdefault('conf', cloud_cn_attrs.get(cn, OrderedDict()))
            dcn.setdefault('vms', OrderedDict())
            dcn.setdefault('vts', [])
        return rdata
    cache_key = __name + '.get_cloud_conf9'
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def get_cloud_conf_by_cns():
    return copy.deepcopy(get_cloud_conf()['cns'])


def get_cloud_conf_by_vts(ttl=PILLAR_TTL):
    def _do():
        data = OrderedDict()
        for cn, cdata in get_cloud_conf_by_cns().items():
            cvms = cdata.pop('vms')
            for vt in cdata['vts']:
                vtdata = data.setdefault(vt, OrderedDict())
                vcndata = vtdata.setdefault(cn, OrderedDict())
                vcnvms = vcndata.setdefault('vms', OrderedDict())
            for vm, vmdata in cvms.items():
                vt = vmdata['vt']
                vtdata = data.setdefault(vt, OrderedDict())
                vcndata = vtdata.setdefault(cn, copy.deepcopy(cdata))
                vcnvms = vcndata.setdefault('vms', OrderedDict())
                vcnvms[vm] = vmdata
        return data
    cache_key = __name + '.get_cloud_conf_by_vts' + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def get_cloud_conf_by_vms(ttl=PILLAR_TTL):
    def _do():
        return copy.deepcopy(get_cloud_conf()['vms'])
    cache_key = __name + '.get_cloud_conf_by_vms' + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def get_cloud_entry_for_cn(id_, default=None):
    if not default:
        default = {}
    return get_cloud_conf_by_cns().get(id_, default)


def get_cloud_conf_for_cn(id_, default=None):
    return get_cloud_entry_for_cn(id_, default=default).get('conf', {})


def get_cloud_conf_for_vt(id_, default=None):
    if not default:
        default = {}
    return get_cloud_conf_by_vts().get(id_, default)


def get_cloud_conf_for_vm(id_, default=None):
    if not default:
        default = {}
    return copy.deepcopy(get_cloud_conf_by_vms().get(id_, default))



def get_db_infrastructure_maps(ttl=PILLAR_TTL):
    '''
    Return a struct::

         {'bms': {'xx-1.yyy.net': ['lxc'],
                  'xx-4.yyy.net': ['lxc']},
         'vms': {'zz.yyy': {'target': 'xx.yyy.net',
                            'vt': 'kvm'},
                 'vv.yyy.net': {'target': 'xx.yyy.net',
                                'vt': 'kvm'},}}
    '''
    def _do():
        non_managed_hosts = __salt__[
            __name + '.query']('non_managed_hosts', {})
        cloud_conf = get_cloud_conf()
        bms = copy.deepcopy(cloud_conf['cns'])
        vms = copy.deepcopy(cloud_conf['vms'])
        cloud_compute_nodes = set()
        cloud_vms = set()
        standalone_hosts = OrderedDict()
        for i, idata in six.iteritems(bms):
            cloud_compute_nodes.add(i)
            for v, vdata in six.iteritems(idata.get('vms', {})):
                cloud_vms.add(v)
            if not (idata['vms'] or idata['vts']):
                standalone_hosts.setdefault(i, {})
        data = {'bms': bms,
                'vms': vms,
                'hosts': sorted(
                    __salt__['mc_utils.uniquify'](
                        [a for a in bms] +
                        [a for a in vms] +
                        [a for a in non_managed_hosts] +
                        [a for a in cloud_compute_nodes])),
                'standalone_hosts': standalone_hosts,
                'cloud_compute_nodes': [a for a in cloud_compute_nodes],
                'cloud_vms': [a for a in cloud_vms]}
        return data
    # no memcached, relies on memoize !
    cache_key = __name + '.get_db_infrastructure_maps' + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [], {}, cache=_cache, key=cache_key, seconds=ttl)


def ips_for(fqdn,
            fail_over=None,
            recurse=None,
            ignore_aliases=None,
            ignore_cnames=None,
            **kw):
    '''
    Get all ip for a domain, try as a FQDN first and then
    try to append the specified domain
    We need a local cache to store the ips resolved from different
    datasource, DO NOT USE QUERY() DIRECTLY HERE

        fail_over
            If FailOver records exists and no ip was found, it will take this
            value.
            If failOver exists and fail_over=true, all ips
            will be returned

    Warning this method is tightly tied to load_network_infrastructure
    '''
    debug = kw.get('debug', None)
    resips = []
    data = load_network(debug=debug)
    if data['raw_db_loading'] is None:
        data = load_raw_network_infrastructure()
    cnames = data['cnames']
    ips = data['ips']
    ips_map = data['ips_map']
    ipsfo = data['ipsfo']
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
        if fqdn in ipsfo:
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
            resips = ips_for(fqdn, recurse=recurse, fail_over=True)
        # for upper tld , check the @ RECORD
        if (
            (not resips) and
            ((not fqdn.startswith('@')) and
             (fqdn.count('.') == 1))
        ):
            resips = ips_for("@" + fqdn, recurse=recurse, fail_over=True)
        if not resips:
            msg = '{0}\n'.format(fqdn)
            if len(recurse) > 1:
                msg += 'recurse: {0}\n'.format(recurse)
            retrieval_error(IPRetrievalError(msg), fqdn, recurse=recurse)

    for ignore in [ignore_aliases, ignore_cnames]:
        if fqdn in ignore:
            ignore.pop(ignore.index(fqdn))
    if (
        data['raw_db_loaded'] and
        (not data['extra_info_loaded']) and
        (data['extra_info_loading'] is None)
    ):
        data = load_network_infrastructure()
        resips = ips_for(fqdn,
                         fail_over=fail_over,
                         recurse=recurse,
                         ignore_aliases=ignore_aliases,
                         ignore_cnames=ignore_cnames,
                         **kw)
        if not data['extra_info_loaded']:
            raise IPRetrievalError(
                'Pb with {0}: data did not load completly'.format(fqdn))
    resips = __salt__['mc_utils.uniquify'](resips)
    return resips


def load_raw_network_infrastructure(ttl=PILLAR_TTL):
    data = load_network()
    if data['raw_db_loaded']:
        return data
    data['raw_db_loading'] = True
    ips = data['ips']
    ipsfo = data['ipsfo']
    ips_map = data['ips_map']
    ipsfo_map = data['ipsfo_map']
    vms = __salt__[__name + '.query']('vms', {})
    cloud_vm_attrs = __salt__[__name + '.query']('cloud_vm_attrs', {})
    dbi = get_db_infrastructure_maps()
    baremetal_hosts = dbi['bms']

    for fqdn in ipsfo:
        if fqdn in ips:
            continue
        ips[fqdn] = ips_for(fqdn, fail_over=True)

    # ADD A Mappings for aliased ips (manual) or over ip failover
    cvms = OrderedDict()
    for vt, targets in vms.items():
        for target, _vms in targets.items():
            if _vms is None:
                log.error('No vms for {0}, error?'.format(target))
                continue
            for _vm in _vms:
                cvms[_vm] = target

    cvalues = cvms.values()
    for host, dn_ip_fos in ipsfo_map.items():
        for ip_fo in dn_ip_fos:
            dn = host.split('.')[0]
            ipfo_dn = ip_fo.split('.')[0]
            ip = ips_for(ip_fo)[0]
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
                    (host not in baremetal_hosts and
                     host not in cvalues) and
                    host not in ips
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
                ips[vm] = ips_for(vm)
            else:
                ips[vm] = ips_for(vm_host)

    # tie extra domains of vms to a A record: part1
    # try to resolve ips for vms but let a chance
    # for the non resolved one to come up in a later time
    # via ips_map
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
            aliases = ips_map.get(domain, [])
            if aliases:
                for alias in aliases:
                    try:
                        for ip in ips_for(alias, fail_over=True):
                            if ip not in dips:
                                dips.append(ip)
                    except IPRetrievalError:
                        continue
            # never append an ip if it was aliased before
            if len(dips):
                continue
            try:
                for ip in ips_for(vm, fail_over=True):
                    if ip not in dips:
                        dips.append(ip)
            except IPRetrievalError:
                continue

    # add all IPS  from aliased ips to main dict
    for fqdn in ips_map:
        if fqdn in ips:
            continue
        ips[fqdn] = ips_for(fqdn)

    # tie extra domains of vms to a A record: part2
    # try to resolve leftover ips
    for vm, _data in cloud_vm_attrs.items():
        domains = _data.get('domains', [])
        if not isinstance(domains, list):
            continue
        for domain in domains:
            dips = ips.setdefault(domain, [])
            # never append an ip of a vm is it is already defined
            if len(dips):
                continue
            aliases = ips_map.get(domain, [])
            if aliases:
                for alias in aliases:
                    try:
                        for ip in ips_for(alias, fail_over=True):
                            if ip not in dips:
                                dips.append(ip)
                    except IPRetrievalError:
                        continue
            # never append an ip if it was aliased before
            if len(dips):
                continue
            # difference with round 1 is that here we fail on
            # IPRetrievalError
            for ip in ips_for(vm, fail_over=True):
                if ip not in dips:
                    dips.append(ip)
    data['raw_db_loading'] = False
    data['raw_db_loaded'] = True
    return data


def ips_canfailover_for(*a, **kw):
    '''
    Get the real ips of a service, and fallback in case on failovers ips
    but do not return ips + failovers ips if there are real ips.
    '''
    try:
        ips = ips_for(*a, **kw)
        if not ips:
            raise IPRetrievalError()
        return ips
    except IPRetrievalError:
        kw['fail_over'] = True
        return ips_for(*a, **kw)


def ip_canfailover_for(*a, **kw):
    '''
    Wrapper to get the first available ip or failover ip
    '''
    return ips_canfailover_for(*a, **kw)[0]


def load_network_infrastructure(ttl=PILLAR_TTL):
    '''
    This loads the structure while validating it for
    reverse ip lookups
    We need a local cache to store the ips resolved from different
    datasource, DO NOT USE QUERY() DIRECTLY HERE

    Warning this method is tightly tied to ips_for
    '''
    data = load_raw_network_infrastructure()
    ips = data['ips']
    ips_map = data['ips_map']
    ipsfo_map = data['ipsfo_map']
    mx_map = __salt__[__name + '.query']('mx_map', {})
    managed_dns_zones = __salt__[__name + '.query']('managed_dns_zones', {})
    get_db_infrastructure_maps()
    cnames = data['cnames']
    if data['extra_info_loaded']:
        return data
    data['extra_info_loading'] = True
    # for each managed dns zone,
    # we load the nameservers ip aliases if they are not explicitly
    # configured but we have enougth information to get them
    nss = get_nss()['all']
    for zone in managed_dns_zones:
        nssz = get_nss_for_zone(zone)
        for nsq, slave in nssz['slaves'].items():
            # special case
            if '.' in slave and zone not in nsq:
                continue
            if nsq not in ips:
                if nsq.endswith(zone) and nsq != slave:
                    nsqs = ips.setdefault(nsq, [])
                    try:
                        sips = ips_canfailover_for(slave)
                    except IPRetrievalError:
                        sips = []
                    for ip in sips:
                        if ip not in nsqs:
                            nsqs.append(ip)
            if slave in cnames and slave not in ips:
                ips[slave] = [ip_canfailover_for(cnames[slave][:-1])]
            if nsq in cnames and slave not in ips:
                ips[slave] = [ip_canfailover_for(cnames[nsq][:-1])]
            if (nsq in ips or nsq in ips_map) and slave not in ips:
                ips[slave] = [ip_canfailover_for(nsq)]
    mxs = []
    for servers in mx_map.values():
        for server in servers:
            mxs.append(server)

    # for:
    #   - @ failover mappings
    #   - nameservers
    #   - mx
    # add a A record where normally we would end up with a CNAME
    for fqdn in ipsfo_map:
        if (fqdn.startswith('@')) or (fqdn in mxs) or (fqdn in nss):
            if fqdn not in ips:
                ips[fqdn] = ips_for(fqdn, fail_over=True)
    data['extra_info_loading'] = False
    data['extra_info_loaded'] = True
    return data


def ip_for(fqdn, *args, **kwa1):
    '''
    Get an ip for a domain, try as a FQDN first and then
    try to append the specified domain

        fail_over
            If FailOver records exists and no ip was found, it will take this
            value.
            If failOver exists and fail_over=true, all ips
            will be returned
    '''
    return ips_for(fqdn, *args, **kwa1)[0]


def rr_entry(fqdn, targets, priority='10', record_type='A'):
    rrs_ttls = __salt__[__name + '.query']('rrs_ttls', {})
    if record_type in ['MX']:
        priority = ' {0}'.format(priority)
    else:
        priority = ''
    fqdn_entry = fqdn
    if fqdn.startswith('@'):
        fqdn_entry = '@'
    elif not fqdn.endswith('.'):
        fqdn_entry += '.'
    ttl = rrs_ttls.get(fqdn_entry, '')
    IN = ''
    if record_type in ['NS', 'MX']:
        IN = ' IN'
    rr = '{0}{1}{2} {3}{4} {5}\n'.format(
        fqdn_entry, ttl, IN, record_type, priority, targets[0])
    for ip in targets[1:]:
        ttl = rrs_ttls.get(fqdn_entry, '')
        if ttl:
            ttl = ' {0}'.format(ttl)
        rr += '       {0}{1}{2} {3}{4} {5}\n'.format(
            fqdn_entry, ttl, IN, record_type, priority, ip)
    rr = '\n'.join([a for a in rr.split('\n') if a.strip()])
    return rr


def rr_a(fqdn, fail_over=None, ttl=PILLAR_TTL):
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
    cache_key = __name + '.rrs_a_{0}_{1}_{2}'.format(fqdn, fqdn, fail_over) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [fqdn, fail_over], {}, cache_key, ttl)


def whitelisted(dn, ttl=PILLAR_TTL):
    '''
    Return all configured NS records for a domain'''
    def _do_whitel(dn):
        allow = __salt__[__name + '.query']('default_allowed_ips_names', {})
        allow = allow.get(dn, allow.get('default', {}))
        w = []
        for fqdn in allow:
            for ip in [a for a in ips_for(fqdn) if a not in w]:
                w.append(ip)
        return w
    cache_key = __name + '.whitelisted_{0}'.format(dn) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do_whitel, [dn], {}, cache_key, ttl)


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


def rrs_txt_for(domain, ttl=PILLAR_TTL):
    '''
    Return all configured NS records for a domain
    '''
    def _do(domain):
        _s = __salt__
        rrs_ttls = _s[__name + '.query']('rrs_ttls', {})
        rrs_txts = _s[__name + '.query']('rrs_txt', {})
        all_rrs = OrderedDict()
        domain_re = re.compile(DOTTED_DOMAIN_PATTERN.format(domain=domain),
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
    cache_key = __name + '.rrs_txt_for_{0}'.format(domain) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [domain], {}, cache_key, ttl)


def rrs_srv_for(domain, ttl=PILLAR_TTL):
    '''
    Return all configured TXT records for a domain
    '''
    def _do(domain):
        _s = __salt__
        rrs_ttls = _s[__name + '.query']('rrs_ttls', {})
        rrs_srvs = _s[__name + '.query']('rrs_srv', {})
        all_rrs = OrderedDict()
        domain_re = re.compile(DOTTED_DOMAIN_PATTERN.format(domain=domain),
                               re.M | re.U | re.S | re.I)
        for fqdn, rrs in rrs_srvs.items():
            if domain_re.search(fqdn):
                srvrrs = all_rrs.setdefault(fqdn, [])
                if isinstance(rrs, basestring):
                    rrs = [rrs]
                dfqdn = fqdn
                if not dfqdn.endswith('.'):
                    dfqdn += '.'
                for rr in rr_entry(
                    fqdn, ['{0}'.format(r) for r in rrs],
                    rrs_ttls,
                    record_type='SRV'
                ).split('\n'):
                    if rr not in srvrrs:
                        srvrrs.append(rr)
        rr = filter_rr_str(all_rrs)
        return rr
    cache_key = __name + '.rrs_srv_for_{0}'.format(domain) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [domain], {}, cache_key, ttl)


def get_nss(ttl=PILLAR_TTL):
    '''
    Get a map of relationship between name servers
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
    def _do():
        _s = __salt__
        dns_servers = {'all': [],
                       'map': OrderedDict(),
                       'masters': OrderedDict(),
                       'slaves': OrderedDict()}
        dns_servers['map'] = _s[__name + '.query'](
            'dns_servers', {}).get('map', {})
        dbdns_zones = _s[__name + '.query']('managed_dns_zones', {})
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
    cache_key = __name + '.get_nss'
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def get_ns_master(id_, dns_servers=None, default=None, ttl=PILLAR_TTL):
    '''
    Grab masters in this form::

        dns_servers:
            zoneid_dn:
                master: fqfn
    '''
    def _do(id_, dns_servers=None, default=None):
        managed_dns_zones = __salt__[__name + '.query'](
            'managed_dns_zones', {})
        if id_ not in managed_dns_zones:
            raise ValueError('{0} is not managed'.format(id_))
        if not dns_servers:
            dns_servers = __salt__[__name + '.query']('dns_servers', {})
        if not default:
            default = dns_servers.get('default', {})
        master = dns_servers.get(id_, OrderedDict()).get('master', None)
        if not master:
            master = default.get('master', None)
        if not master:
            raise ValueError('No master for {0}'.format(id_))
        if not isinstance(master, basestring):
            raise ValueError(
                '{0} is not a string for dns master {1}'.format(
                    master, id_))
        return master
    cache_key = __name + '.get_ns_master_{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [id_, dns_servers, default], {}, cache_key, ttl)


def is_failover(ip, ttl=PILLAR_TTL):
    def _do(ip):
        if __salt__['mc_network.is_ip'](ip):
            ndb = load_network_infrastructure()
            for name, ips in six.iteritems(ndb['ipsfo']):
                if ip in ips:
                    return True
        return False
    cache_key = __name + '.is_failover{0}'.format(ip) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [ip], {}, cache_key, ttl)


def get_names_for_failover(ip, ttl=PILLAR_TTL):
    def _do(ip):
        if is_failover(ip):
            ndb = load_network_infrastructure()
            names = []
            for name, ips in six.iteritems(ndb['ipsfo']):
                if ip in ips and name not in names:
                    names.append(name)
        return names
    cache_key = __name + '.get_names_for_failover{0}'.format(ip) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [ip], {}, cache_key, ttl)


def get_servername_for_ip(ip, ttl=PILLAR_TTL, no_vm=False):
    '''
    For a given ip, or failover ip, retrieve the underthehood linked server or
    vm name.
    '''
    def _do(ip):
        name = None
        if __salt__['mc_network.is_ip'](ip):
            ndb = load_network_infrastructure()
            db = get_db_infrastructure_maps()
            if is_failover(ip):
                # first try the ipsfo_map:
                for ipfo_name in get_names_for_failover(ip):
                    if ipfo_name in db['hosts']:
                        return ipfo_name
                    for item, ips in six.iteritems(ndb['ipsfo_map']):
                        if ipfo_name in ips and item in db['hosts']:
                            name = item
                        if name:
                            break
                    if name:
                        break
            else:
                # then fallback on ips
                for item, ips in six.iteritems(ndb['ips']):
                    if ip in ips and item in db['hosts']:
                        name = item
                    if name:
                        break
        return name
    cache_key = __name + '.get_servername_for_ip{0}'.format(ip) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [ip], {}, cache_key, ttl)


def get_servername_for(id_or_ip, ttl=PILLAR_TTL):
    '''
    For a given ip, or failover ip, or dns name
    retrieve the server or vm where is directly linked the
    aforementioned id/ip.  Be aware that in cases of VMS, the public ip
    can be associated to the baremetal and not the vm
    and so the returned name can obviously be the baremetal one.
    '''
    def _do(id_or_ip):
        ips = []
        if __salt__['mc_network.is_ip'](id_or_ip):
            ips.append(id_or_ip)
        else:
            ips.extend(resolve_ips(id_or_ip))
        for ip in ips:
            name = get_servername_for_ip(ip)
            if name:
                return name
    cache_key = __name + '.get_servername_for{0}'.format(id_or_ip) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [id_or_ip], {}, cache_key, ttl)


def get_raw_ns_slaves(id_, dns_servers=None, default=None, ttl=PILLAR_TTL):
    '''
    Grab slaves in this form::

        dns_servers:
            zoneid_dn:
                slaves:
                    - fqdn (aliased ip name, ip failover name or baremetal
                             server address name)

    This returns a map between the NS record name and it's associated server
    name::

        ns1.makina-corpus.net:
            ovh-r5-2.makina-corpus.net
        ns2.makina-corpus.net:
            online-dc3-4.makina-corpus.net
        ns3.makina-corpus.net:
            online-dc3-3.makina-corpus.net
    '''
    def _do(id_, dns_servers=None, default=None):
        managed_dns_zones = __salt__[
            __name + '.query']('managed_dns_zones', {})
        if id_ not in managed_dns_zones:
            raise ValueError('{0} is not managed'.format(id_))
        if not dns_servers:
            dns_servers = __salt__[__name + '.query']('dns_servers', {})
        if not default:
            default = dns_servers.get('default', {})
        rlslaves = dns_servers.get(
            id_, OrderedDict()).get('slaves', OrderedDict())
        if not rlslaves:
            rlslaves = default.get('slaves', OrderedDict())
        if rlslaves and not isinstance(rlslaves, list):
            raise ValueError('Invalid format for slaves for {0}'.format(id_))
        lslaves = OrderedDict()
        for item in rlslaves:
            # old id: FQDN format (retrocompat)
            if isinstance(item, dict):
                pass
            elif isinstance(item, six.string_types):
                item = {item: item}
            else:
                raise ValueError(
                    'Invalid format for ns slaves: {0}'.format(id_))
            for k, val in six.iteritems(item):
                lslaves[k] = val
        return lslaves
    cache_key = __name + '.get_raw_ns_slaves_{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [id_, dns_servers, default], {}, cache_key, ttl)


def get_ns_slaves(id_, dns_servers=None, default=None, ttl=PILLAR_TTL):
    def _do(id_, dns_servers=None, default=None):
        lslaves = get_raw_ns_slaves(id_,
                                    dns_servers=dns_servers,
                                    default=default)
        slaves = OrderedDict()
        for slave in [lslaves]:
            for nsid in [a for a in slave]:
                target = slave[nsid]
                ns_fqdn = nsid
                if not isinstance(nsid, basestring):
                    raise ValueError(
                        '{0} is not a valid dn for nameserver in '
                        '{1}'.format(nsid, id_))
                if not isinstance(target, basestring):
                    raise ValueError(
                        '{0} is not a valid dn for nameserver target in '
                        '{1}'.format(target, id_))
                if '.' not in nsid:
                    ns_fqdn = '{0}.{1}'.format(nsid, id_)
                if '.' not in target:
                    target = '{0}.{1}'.format(target, id_)
                slaves[ns_fqdn] = target
        return slaves
    cache_key = __name + '.get_ns_slaves_{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [id_, dns_servers, default], {}, cache_key, ttl)


def get_nss_for_zone(id_, ttl=PILLAR_TTL):
    '''
    Return all masters and slaves for a zone

    If there is a master but no slaves, the master becomes also the only slave
    for that zone

    Slave in makina-states means a name server which is exposed to outside
    world via an NS record.
    '''
    def _do_getnssforzone(id_):
        dns_servers = __salt__[__name + '.query']('dns_servers', {})
        master = get_ns_master(id_, dns_servers=dns_servers)
        slaves = get_ns_slaves(id_, dns_servers=dns_servers)
        if not master and not slaves:
            raise ValueError('no ns information for {0}'.format(id_))
        data = {'master': master, 'slaves': slaves}
        return data
    cache_key = __name + '.get_nss_for_zone_{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do_getnssforzone, [id_], {}, cache_key, ttl)


def resolve_ips(name, fail_over=True, dns_query=True, ttl=PILLAR_TTL):
    '''
    Try to resolve the ips of a name
    either by the database and maybe on a DNS query fallback
    if not found
    '''
    def _do(name, fail_over, dns_query):

        # maybe we are on a failover ip, get the alternatives ips
        # of this host to check
        try:
            # if the ip is in pillar, get that
            zips = ips_for(name, fail_over=fail_over)
        except IPRetrievalError:
            zips = []
        if dns_query and not zips:
            # else use a dns query to try to get it
            try:
                zips = socket.gethostbyaddr(name)[2]
            except socket_errors:
                zips = []
        return zips
    cache_key = __name + '.resolve_ips{0}{1}{2}'.format(
        name, fail_over, dns_query) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [name, fail_over, dns_query], {}, cache_key, ttl)


def resolve_ip(name, fail_over=True, dns_query=True):
    '''
    Get the first resolved IP of ips_resolve(*a)
    '''
    return resolve_ip(name, fail_over=fail_over, dns_query=dns_query)[0]


def get_slaves_for(id_, ttl=PILLAR_TTL):
    '''
    Get all public exposed dns servers slaves
    for a specific dns master
    Return something like::

        {
            all: [all slaves related to this master],
            z: {
                {zone domains: [list of slaves related to this zone]
               }
        }

    '''
    def _do(id_):
        allslaves = {'z': OrderedDict(), 'all': []}
        this_ips = resolve_ips(id_, fail_over=True)
        for zone in __salt__[__name + '.query']('managed_dns_zones', {}):
            zi = get_nss_for_zone(zone)
            found = id_ == zi['master']
            if not found:
                zips = resolve_ips(zi['master'])
                if not zips:
                    continue
                # search if one ip of this host matches the list of the
                # zone master's ips
                for ip in this_ips:
                    if ip in zips:
                        found = True
                        break
            if found:
                slaves = allslaves['z'].setdefault(zone, [])
                for nsid, fqdn in zi['slaves'].items():
                    if fqdn not in allslaves['all']:
                        allslaves['all'].append(fqdn)
                    if fqdn not in slaves:
                        slaves.append(fqdn)
        allslaves['all'].sort()
        return allslaves
    cache_key = __name + '.get_slaves_for_{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_ns(domain, ttl=PILLAR_TTL):
    '''
    Get the first configured public name server for domain
    '''
    def _do(domain):
        return get_nss_for_zone(domain)[0]
    cache_key = __name + '.get_ns_{0}'.format(domain) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [domain], {}, cache_key, ttl)


def get_slaves_zones_for(fqdn, ttl=PILLAR_TTL):
    def _do(fqdn):
        zones = {}
        this_ips = resolve_ips(fqdn, fail_over=True)
        for zone in __salt__[__name + '.query']('managed_dns_zones', {}):
            zi = get_nss_for_zone(zone)
            slaves = zi['slaves'].values()
            found = fqdn in slaves
            if not found:
                for slave in zi['slaves'].values():
                    zips = resolve_ips(slave)
                    for ip in this_ips:
                        if ip in zips:
                            found = True
                            break
            if found:
                zones[zone] = zi['master']
        return zones
    cache_key = __name + '.get_slaves_zones_for_{0}'.format(fqdn) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [fqdn], {}, cache_key, ttl)


def rrs_mx_for(domain, ttl=PILLAR_TTL):
    '''
    Return all configured MX records for a domain
    '''
    def _do(domain):
        mx_map = __salt__[__name + '.query']('mx_map', {})
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
    cache_key = __name + '.rrs_mx_for_{0}'.format(domain) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [domain], {}, cache_key, ttl)


def rrs_ns_for(domain, ttl=PILLAR_TTL):
    '''
    Return all configured NS records for a domain
    '''
    def _do(domain):
        rrs_ttls = __salt__[__name + '.query']('rrs_ttls', {})
        all_rrs = OrderedDict()
        servers = get_nss_for_zone(domain)
        slaves = servers['slaves']
        if not slaves:
            rrs = all_rrs.setdefault(domain, [])
            rrs.append(
                rr_entry('@', ["{0}.".format(servers['master'])],
                         rrs_ttls, record_type='NS'))
        for ns_map, fqdn in slaves.items():
            # ensure NS A mapping is there if it is on same domain
            if fqdn.startswith(domain):
                ip = ips_for(fqdn)
                assert len(ip)
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
    cache_key = __name + '.rrs_ns_for_{0}'.format(domain) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [domain], {}, cache_key, ttl)


def rrs_a_for(domain, ttl=PILLAR_TTL):
    '''
    Return all configured A records for a domain
    '''
    def _do(domain):
        db = load_network_infrastructure()
        rrs_ttls = __salt__[__name + '.query']('rrs_ttls', {})
        ips = db['ips']
        all_rrs = OrderedDict()
        domain_re = re.compile(DOTTED_DOMAIN_PATTERN.format(domain=domain),
                               re.M | re.U | re.S | re.I)
        # add all A from simple ips
        for fqdn in ips:
            if domain_re.search(fqdn):
                rrs = all_rrs.setdefault(fqdn, [])
                if not ips[fqdn]:
                    raise RRError('No ip for {0}'.format(fqdn))
                for rr in rr_entry(
                    fqdn, ips[fqdn], rrs_ttls
                ).split('\n'):
                    if rr not in rrs:
                        rrs.append(rr)
        rr = filter_rr_str(all_rrs)
        return rr
    cache_key = __name + '.rrs_a_for_{0}'.format(domain) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [domain], {}, cache_key, ttl)


def rrs_raw_for(domain, ttl=PILLAR_TTL):
    '''
    Return all configured TXT records for a domain
    '''
    def _do(domain):
        # add all A from simple ips
        load_network_infrastructure()
        rrs_raw = __salt__[__name + '.query']('rrs_raw', {})
        all_rrs = OrderedDict()
        domain_re = re.compile(DOTTED_DOMAIN_PATTERN.format(domain=domain),
                               re.M | re.U | re.S | re.I)
        for fqdn in rrs_raw:
            if domain_re.search(fqdn):
                rrs = all_rrs.setdefault(fqdn, [])
                for rr in rrs_raw[fqdn]:
                    if rr not in rrs:
                        rrs.append(rr)
        rr = filter_rr_str(all_rrs)
        return rr
    cache_key = __name + '.rrs_raw_for_{0}'.format(domain) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [domain], {}, cache_key, ttl)


def rrs_cnames_for(domain, ttl=PILLAR_TTL):
    '''
    Return all configured CNAME records for a domain
    '''
    def _do(domain):
        db = load_network_infrastructure()
        managed_dns_zones = __salt__[
            __name + '.query']('managed_dns_zones', {})
        rrs_ttls = __salt__[__name + '.query']('rrs_ttls', {})
        ipsfo = db['ipsfo']
        ipsfo_map = db['ipsfo_map']
        ips_map = db['ips_map']
        cnames = db['cnames']
        ips = db['ips']
        all_rrs = OrderedDict()
        domain_re = re.compile(DOTTED_DOMAIN_PATTERN.format(domain=domain),
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
                        tcname.endswith(domain) and (
                            tcname in ips_map or
                            tcname in ipsfo_map or
                            tcname in ipsfo)
                    ):
                        checks.append(tcname)
                for atest in checks:
                    # raise exc if not found
                    # but only if we manage the domain of the targeted
                    # rr
                    try:
                        ips_for(atest, fail_over=True)
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
                if cname.endswith(domain) and not cname.endswith('.'):
                    dcname = '{0}.'.format(dcname)
                ttl = rrs_ttls.get(cname, '')
                entry = '{0} {1} CNAME {2}'.format(
                    dcname, ttl, rr)
                if entry not in rrs:
                    rrs.append(entry)
        rr = filter_rr_str(all_rrs)
        return rr
    cache_key = __name + '.rrs_cnames_for_{0}'.format(domain) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [domain], {}, cache_key, ttl)


def serial_for(domain,
               serial=None,
               autoinc=True,
               force_serial=None,
               ttl=PILLAR_TTL):
    '''
    Get the serial for a DNS zone

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
        - at the end, we try to reach the nameservers in the wild
          to adapt our serial if it is too low or too high
    '''
    def _do(domain, serial=None, ttl=PILLAR_TTL):
        serials = __salt__[__name + '.query']('dns_serials', {})
        # load the local pillar dns registry
        dns_reg = __salt__['mc_macros.get_local_registry'](
            'dns_serials', registry_format='pack')
        dns_failures = __salt__['mc_macros.get_local_registry'](
            'dns_serials_failures', registry_format='pack')
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
        dnow = datetime.datetime.now()
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
        # only update the ttl on expiraton or creation
        if stale:
            dns_reg[ttl_key] = time.time()
        if force_serial:
            serial = force_serial
        # in any case, if NS in the domain are reachable,
        # we query each ones to get the max(serial) + 1
        # this avoid real situation errors and serial
        # mismatch between master and slaves
        # If our serial is inferior, we take this serial as a value
        now = datetime.datetime.now()
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = 10
            resolver.lifetime = 10
            aquery = resolver.query(domain, 'NS', tcp=True)
            dns_serial = 0
            for qns in aquery:
                ns = qns.to_text()
                if not ns.endswith('.'):
                    ns += domain + '.'
                ns = ns[:-1]
                request = dns.message.make_query(domain, dns.rdatatype.SOA)
                do_skip = False
                t10 = datetime.timedelta(minutes=10)
                try:
                    nsip = socket.gethostbyname(ns)
                except Exception:
                    nsip = ns
                # if a nameserver fails three times
                # ignore it for 10 minutes
                if nsip in dns_failures:
                    failure = dns_failures[nsip]
                    try:
                        odate = datetime.datetime.strptime(
                            failure['date'][:-7], '%Y-%m-%dT%H:%M:%S')
                    except Exception:
                        odate = now
                    if failure['skip'] and (now - odate < t10):
                        do_skip = True
                        log.error(
                            'nameserver {0}/{1} is skipped 10minutes, too much'
                            ' failures'.format(ns, nsip))
                    if now - odate >= t10:
                        dns_failures.pop(ns, None)
                if not do_skip:
                    res = dns.query.tcp(request, ns, timeout=5)
                    for answer in res.answer:
                        for soa in answer:
                            if soa.serial > dns_serial:
                                dns_serial = soa.serial
                    if ns in dns_failures:
                        dns_failures.pop(ns, None)
            if dns_serial != serial and dns_serial > 0:
                serial = dns_serial
        except Exception, ex:
            hasns, nsip, failure = True, '', {}
            trace = traceback.format_exc()
            try:
                nsip = socket.gethostbyname(ns)
            except Exception:
                try:
                    nsip = ns
                except UnboundLocalError:
                    hasns = False
            if hasns:
                failure = dns_failures.setdefault(
                    nsip,
                    {'date': now.isoformat(), 'skip': False, 'count': 0})
                failure['count'] += 1
                if failure['count'] > 3:
                    failure['skip'] = True
                log.error('DNSSERIALS: {0}: {1} failures: {2}'.format(
                    ns, nsip, failure))
            log.error('DNSSERIALS: {0}'.format(ex))
            log.error('DNSSERIALS: {0}'.format(domain))
            log.error(trace)
        # try to respect the Year-mo-da-xx convention
        # if serial is way behind the current day
        ymdx = int('{0:04d}{1:02d}{2:02d}'.format(
            dnow.year, dnow.month, dnow.day))
        if ymdx > (serial//100):
            serial = (ymdx * 100)
        if not force_serial:
            serial += 1
        dns_reg[domain] = serial
        __salt__['mc_macros.update_local_registry'](
            'dns_failures', dns_failures, registry_format='pack')
        __salt__['mc_macros.update_local_registry'](
            'dns_serials', dns_reg, registry_format='pack')
        return serial
    return _do(domain, serial, ttl=ttl)


def rrs_for(domain, aslist=False):
    '''
    Return all configured records for a domain
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
        rrs_srv_for(domain) + '\n' +
        rrs_a_for(domain) + '\n' +
        rrs_cnames_for(domain)
    )
    if aslist:
        rr = [a.strip() for a in rr.split('\n') if a.strip()]
    return rr


def get_ldap(ttl=PILLAR_TTL):
    '''
    Get a map of relationship between name servers
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
    def _do():
        _s = __salt__
        data = OrderedDict()
        masters = data.setdefault('masters', OrderedDict())
        slaves = data.setdefault('slaves', OrderedDict())
        default = _s[__name + '.query']('ldap_maps', {}).get(
            'default', OrderedDict())
        for kind in ['masters', 'slaves']:
            for server, adata in _s[
                __name + '.query'
            ]('ldap_maps', {}).get(kind, OrderedDict()).items():
                sdata = data[kind][server] = copy.deepcopy(adata)
                for k, val in default.items():
                    sdata.setdefault(k, val)
                sdata.setdefault('cert_domain', server)
                # maybe generate and get the ldap certificates info
        rids = {}
        slavesids = [a for a in slaves]
        slavesids.sort()
        for server in slavesids:
            adata = copy.deepcopy(slaves.get('default', {}))
            adata.update(slaves[server])
            master = adata.setdefault('master', 'localhost')
            master_port = adata.setdefault('master_port', '389')
            srepl = adata.setdefault('syncrepl', OrderedDict())
            if masters and not master:
                adata['master'] = [a for a in masters][0]
            if 'provider' not in srepl and not adata['master']:
                slaves.pop(server)
                continue
            rid = rids.setdefault(master, 100) + 1
            rids[master] = rid
            srepl.setdefault('provider',
                             'ldap://{master}:{port}'.format(
                                 master=master, port=master_port))
            srepl['{0}rid'] = '{0}'.format(rid)
            slaves[server] = adata
        return data
    cache_key = __name + '.getldap' + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def get_slapd_conf(id_, ttl=PILLAR_TTL):
    '''
    Return pillar information to configure makina-states.services.dns.slapd
    '''
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_slapd', True):
            return {}
        is_master = is_ldap_master(id_)
        is_slave = is_ldap_slave(id_)
        if is_master and is_slave:
            raise ValueError(
                'Cant be at the same time'
                ' master and ldap slave: {0}'.format(id_))
        conf = get_ldap()
        data = OrderedDict()
        if is_master:
            data = conf['masters'][id_]
            data['mode'] = 'master'
        elif is_slave:
            data = conf['slaves'][id_]
            data['mode'] = 'slave'
        rdata = OrderedDict()
        if data:
            rdata['makina-states.services.dns.slapd'] = True
            for k in data:
                rdata[
                    'makina-states.services.dns.slapd.{0}'.format(k)
                ] = data[k]
        return rdata
    cache_key = __name + '.get_ldap_conf_for_{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def is_ldap_slave(id_, ttl=PILLAR_TTL):
    def _do(id_):
        if is_managed(id_) and id_ in get_ldap()['slaves']:
            return True
        return False
    cache_key = __name + '.is_ldap_slave_{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def is_ldap_master(id_, ttl=PILLAR_TTL):
    def _do(id_):
        if is_managed(id_) and id_ in get_ldap()['masters']:
            return True
        return False
    cache_key = __name + '.is_ldap_master_{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_ldap_configuration(id_=None, ttl=PILLAR_TTL):
    '''
    Ldap client configuration
    '''
    def _do(id_, sysadmins=None):
        configuration_settings = __salt__[
            __name + '.query']('ldap_configurations', {})
        data = copy.deepcopy(configuration_settings.get('default', {}))
        if id_ in configuration_settings:
            data = __salt__['mc_utils.dictupdate'](
                data, configuration_settings.get(id_, {}))
        return data
    cache_key = __name + '.get_ldap_configuration{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_configuration(id_=None, ttl=PILLAR_TTL):
    def _do(id_, mid):
        _s = __salt__
        _settings = _s[__name + '.query']('configurations', {})
        data = copy.deepcopy(_settings.get('default', {}))
        if id_ in _settings:
            data = _s['mc_utils.dictupdate'](data, _settings[id_])
        mdn = mid.split('.')[1:]
        if not mdn:
            mdn = ['local']
        mdn = '.'.join(mdn)
        data.setdefault('default_env', 'prod')
        data.setdefault('master', mid == id_)
        data.setdefault('domain', mdn)
        return data
    cache_key = __name + '.get_configuration4_{0}'.format(id_) + CACHE_INC_TOKEN
    mid = minion_id()
    return __salt__['mc_utils.memoize_cache'](
        _do, [id_, mid], {}, cache_key, ttl)


def get_snmpd_settings(id_=None, ttl=PILLAR_TTL):
    def _do(id_, sysadmins=None):
        gconf = get_configuration(id_)
        if not gconf.get('manage_snmpd', False):
            return {}
        snmpd_settings = __salt__[__name + '.query']('snmpd_settings', {})
        data = copy.deepcopy(snmpd_settings['default'])
        if id_ in snmpd_settings:
            data = __salt__['mc_utils.dictupdate'](data, snmpd_settings[id_])
        return data
    cache_key = __name + '.get_snmpd_settings_{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_ms_iptables_conf(id_, ttl=PILLAR_TTL):

    def _do(id_):
        _s = __salt__
        qry = _s[__name + '.query']
        gconf = get_configuration(id_)
        ms_iptables_overrides = qry('ms_iptables_overrides', {})
        if gconf.get('manage_ms_iptables', MS_IPTABLES_MANAGED):
            # configure
            pass
        elif id_ not in ms_iptables_overrides:
            return {}
        is_ldap = is_ldap_master(id_) or is_ldap_slave(id_)
        is_dns = is_dns_master(id_) or is_dns_slave(id_)
        p = 'makina-states.services.firewall.ms_iptables'
        rdata = OrderedDict([(p, True)])
        if is_ldap:
            rdata[p + '.no_slapd'] = False
        if is_dns:
            rdata[p + '.no_bind'] = False
        prefix = p + '.'
        for param, value in ms_iptables_overrides.get(id_, {}).items():
            rdata[prefix + param] = value
        return rdata
    cache_key = __name + '.get_ms_iptables_conf5{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_firewalld_conf(id_, ttl=PILLAR_TTL):

    def _do(id_):
        _s = __salt__
        gconf = get_configuration(id_)
        if get_ms_iptables_conf(id_):
            return {}
        if not gconf.get('manage_firewalld', FIREWALLD_MANAGED):
            return {}
        p = 'makina-states.services.firewall.firewalld'
        prefix = p + '.'
        qry = _s[__name + '.query']
        # allowed_ips = _s[__name + '.whitelisted'](id_)
        firewalld_overrides = qry('firewalld_overrides', {})
        rdata = OrderedDict([
            (p, True),
            # to smelly, whitelist too much with firewlld,
            # use specific rules for specific case, no real needs
            #    (prefix + 'trusted_networks', allowed_ips)
        ])
        pservices = rdata.setdefault(prefix+'public_services-append', [])
        is_ldap = is_ldap_master(id_) or is_ldap_slave(id_)
        is_dns = is_dns_master(id_) or is_dns_slave(id_)
        if is_ldap:
            for i in ['ldap', 'ldaps']:
                if i not in pservices:
                    pservices.append(i)
        if is_dns:
            for i in ['dns']:
                if i not in pservices:
                    pservices.append(i)
        buf = OrderedDict()
        for param, value in firewalld_overrides.get(id_, {}).items():
            buf[prefix + param] = value
        rdata = __salt__['mc_utils.dictupdate'](rdata, buf)
        return rdata
    cache_key = __name + '.get_firewalld_conf5{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_shorewall_settings(id_=None, ttl=PILLAR_TTL):
    def _do(id_, sysadmins=None):
        gconf = get_configuration(id_)
        managed = gconf.get('manage_shorewall', True)
        if gconf.get('manage_firewalld', FIREWALLD_MANAGED):
            managed = False
        if not managed:
            return {}
        qry = __salt__[__name + '.query']
        allowed_ips = __salt__[__name + '.whitelisted'](id_)
        shorewall_overrides = qry('shorewall_overrides', {})
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
        for i in [a for a in restrict]:
            if restrict[i] == 'net:':
                restrict[i] = 'fw:127.0.0.1'
        restrict_ssh = gconf.get('manage_ssh_ip_restrictions', False)
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
        if is_salt_managed(id_):
            for param, val in restrict.items():
                shw_params[p_param.format(param.upper())] = val
        is_ldap = is_ldap_master(id_) or is_ldap_slave(id_)
        if is_ldap:
            shw_params[p_param.format('LDAP')] = 'all'
        for param, value in shorewall_overrides.get(id_, {}).items():
            param = 'makina-states.services.firewall.shorewall.' + param
            shw_params[param] = value
        return shw_params
    cache_key = __name + '.get_shorewall_settings3_{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_removed_keys(id_=None, ttl=PILLAR_TTL):
    def _do(id_, removed=None):
        removed_keys_map = __salt__[__name + '.query']('removed_keys_map', {})
        keys_map = __salt__[__name + '.query']('keys_map', {})
        skeys = []
        removed = removed_keys_map.get(
            id_, removed_keys_map.get('default', []))
        for k in removed:
            keys = keys_map.get(k, [])
            for key in keys:
                if key not in skeys:
                    skeys.append(key)
        return skeys
    cache_key = __name + '.get_removed_keys{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_sysadmins_keys(id_=None, ttl=PILLAR_TTL):
    def _do(id_, sysadmins=None):
        gconf = get_configuration(id_)
        if not gconf.get('manage_ssh_keys', True):
            return {}
        sysadmins_keys_map = __salt__[__name + '.query']('sysadmins_keys_map', {})
        keys_map = __salt__[__name + '.query']('keys_map', {})
        skeys = []
        sysadmins = sysadmins_keys_map.get(
            id_, sysadmins_keys_map.get('default', []))
        if 'infra' not in sysadmins:
            sysadmins.append('infra')
        for k in sysadmins:
            keys = keys_map.get(k, [])
            for key in keys:
                if key not in skeys:
                    skeys.append(key)
        return skeys
    cache_key = __name + '.get_sysadmin_keys_{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def delete_password_for(id_, user='root', ttl=PILLAR_TTL):
    '''
    Cleanup a password entry from the local password database
    '''
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


def get_password(id_, user='root', ttl=PILLAR_TTL, regenerate=False, length=12,
                 force=False):
    '''
    Return user/password mappings for a particular host from
    a global pillar passwords map. Create it if not done
    '''
    def _do(id_, user='root'):
        db_reg = __salt__[__name + '.query']('passwords_map', {})
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
            (pw is None) or
            (regenerate and (user not in db_id)) or
            force
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
        return {'clear': pw, 'crypted': cpw}
    if force or regenerate:
        return _do(id_, user)
    cache_key = __name + '.get_passwords_for_{0}_{1}1'.format(id_, user)
    return __salt__['mc_utils.memoize_cache'](
        _do, [id_, user], {}, cache_key, ttl)


def get_passwords(id_, force=False, ttl=PILLAR_TTL):
    '''
    Return user/password mappings for a particular host from
    a global pillar passwords map
    Take in priority pw from the db map
    But if does not exists in the db, lookup inside the local one
    If stiff non found, generate it and store in in local
    '''
    def _do(id_, force):
        defaults_users = ['root', 'sysadmin']
        pw_reg = __salt__['mc_macros.get_local_registry'](
            'passwords_map', registry_format='pack')
        db_reg = __salt__[__name + '.query']('passwords_map', {})
        users, crypted = [], {}
        pw_id = pw_reg.setdefault(id_, {})
        db_id = db_reg.setdefault(id_, {})
        for users_list in [pw_id, db_id, defaults_users]:
            for user in users_list:
                if user not in users:
                    users.append(user)
        for user in users:
            pws = get_password(id_, user, force=force)
            pw = pws['clear']
            cpw = pws['crypted']
            crypted[user] = cpw
            pw_id[user] = pw
            db_id[user] = pw
        passwords = {'clear': pw_id, 'crypted': crypted}
        return passwords
    cache_key = __name + '.get_passwords_2{0}{1}'.format(id_, force)
    return __salt__['mc_utils.memoize_cache'](
        _do, [id_, force], {}, cache_key, ttl)


def regenerate_passwords(ids_=None, users=None):
    pw_reg = copy.deepcopy(
        __salt__['mc_macros.get_local_registry'](
            'passwords_map', registry_format='pack')
    )
    if ids_ and not isinstance(ids_, list):
        ids_ = ids_.split(',')
    if users and not isinstance(users, list):
        users = users.split(',')
    for pw_id in [a for a in pw_reg]:
        data = pw_reg[pw_id]
        if ids_ and pw_id not in ids_:
            continue
        for u, pw, in copy.deepcopy(data).items():
            print(pw_id, u)
            if users and u not in users:
                continue
            get_password(pw_id, u, force=True)


def get_ssh_groups(id_=None, ttl=PILLAR_TTL):
    def _do_ssh_grp(id_, sysadmins=None):
        db_ssh_groups = __salt__[__name + '.query']('ssh_groups', {})
        ssh_groups = db_ssh_groups.get(
            id_, db_ssh_groups['default'])
        for group in db_ssh_groups['default']:
            if group not in ssh_groups:
                ssh_groups.append(group)
        return ssh_groups
    cache_key = __name + '.get_ssh_groups_{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do_ssh_grp, [id_], {}, cache_key, ttl)


def get_sudoers(id_=None, ttl=PILLAR_TTL):
    def _do_sudoers(id_, sysadmins=None):
        gconf = get_configuration(id_)
        if not gconf.get('manage_sudoers', True):
            return {}
        sudoers_map = __salt__[__name + '.query']('sudoers_map', {})
        sudoers = sudoers_map.get(id_, [])
        if is_salt_managed(id_):
            for s in sudoers_map['default']:
                if s not in sudoers + ['infra']:
                    sudoers.append(s)
        else:
            sudoers = []
        return sudoers
    cache_key = __name + '.get_sudoers_{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do_sudoers, [id_], {}, cache_key, ttl)


def backup_default_configuration_type_for(id_, ttl=PILLAR_TTL):
    def _do(id_):
        db = get_db_infrastructure_maps()
        confs = __salt__[__name + '.query'](
            'backup_configuration_map', {})
        if id_ not in __salt__[
            __name + '.query'
        ]('non_managed_hosts', {}):
            if id_ in db['vms']:
                id_ = 'default-vm'
            else:
                id_ = 'default'
        else:
            id_ = 'default'
        return confs.get(id_, None)
    cache_key = __name + '.backup_default_configuration_type_for{0}'.format(
        id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def backup_configuration_type_for(id_, ttl=PILLAR_TTL):
    def _do(id_):
        confs = __salt__[__name + '.query']('backup_configuration_map', {})
        qconfs = __salt__[__name + '.query']('backup_configurations', {})
        # for trivial joins (on id_, do it automatically)
        if not confs.get(id_, None) and id_ in qconfs:
            confs[id_] = id_
        conf = confs.get(id_, None)
        return conf
    cache_key = __name + '.backup_configuration_type_for{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def backup_configuration_for(id_, ttl=PILLAR_TTL):
    def _do(id_):
        # load database object cache
        get_db_infrastructure_maps()
        _s = __salt__
        default_conf_id = _s[
            __name + '.backup_default_configuration_type_for'](id_)
        confs = _s[__name + '.query']('backup_configurations', {})
        conf_id = _s[__name + '.backup_configuration_type_for'](id_)
        data = OrderedDict()
        if (
            id_ not in _s[__name + '.query']('non_managed_hosts', []) and
            not default_conf_id
        ):
            if id_ in get_cloud_conf_by_vms():
                t = 'vm'
            else:
                t = 'baremetal'
            conf = confs.get(t, None)
            if not conf:
                raise ValueError('No backup info for {0}'.format(id_))
        if (
            id_ in _s[__name + '.query']('non_managed_hosts', []) and
            not conf_id
        ):
            conf_id = _s[__name + '.backup_configuration_type_for'](
                'default')
            # raise ValueError(
            #    'No backup info for {0}'.format(id_))
        # load default conf
        default_conf = copy.deepcopy(confs.get(default_conf_id, OrderedDict()))
        conf = copy.deepcopy(confs.get(conf_id, OrderedDict()))
        for k in [a for a in default_conf if a.startswith('add_')]:
            adding = k.split('add_', 1)[1]
            ddata = data.setdefault(adding, [])
            ddata.extend([a for a in default_conf[k] if a not in ddata])
        data = _s['mc_utils.dictupdate'](data, default_conf)
        # load per host conf
        if conf_id != default_conf_id:
            for k in [a for a in conf if a.startswith('add_')]:
                adding = k.split('add_', 1)[1]
                ddata = data.setdefault(adding, [])
                ddata.extend([a for a in conf[k] if a not in ddata])
            data = _s['mc_utils.dictupdate'](data, conf)
        for cfg in [default_conf, conf]:
            for remove_key in ['remove', 'delete', 'del']:
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
    cache_key = __name + '.backup_configuration_for{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def backup_server_for(id_, ttl=PILLAR_TTL):
    def _do(id_):
        confs = __salt__[__name + '.query']('backup_server_map', {})
        sconfs = __salt__[__name + '.query']('backup_servers', {})
        default = confs.get('default')
        if not default:
            if sconfs:
                default = [a for a in sconfs][0]
            else:
                raise ValueError('No default backup serveur')
        return confs.get(id_, default)
    cache_key = __name + '.backup_server_for{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def backup_server(id_, ttl=PILLAR_TTL):
    def _do(id_):
        confs = __salt__[__name + '.query']('backup_servers', {})
        return confs[id_]
    cache_key = __name + '.backup_server{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def is_burp_server(id_, ttl=PILLAR_TTL):
    def _do(id_):
        confs = __salt__[__name + '.query']('backup_servers', {})
        return 'burp' in confs.get(id_, {}).get('types', [])
    cache_key = __name + '.is_burp_server{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def backup_server_settings_for(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_backup_server', True):
            return {}
        data = OrderedDict()
        db = get_db_infrastructure_maps()
        load_network_infrastructure()
        _s = __salt__
        # pretendants are all managed baremetals excluding non managed
        # hosts and current backup server
        # db['non_managed_hosts'] + [id_]
        try:
            backup_excluded = query('backup_excluded', [])
            if not isinstance(backup_excluded, list):
                raise ValueError('{0} is not a list for'
                                 ' backup_excluded'.format(backup_excluded))
        except Exception:
            trace = traceback.format_exc()
            log.error(trace)
            backup_excluded = []
        backup_excluded.extend(['default', 'default-vm', id_])
        manual_hosts = _s[__name + '.query']('backup_manual_hosts', [])
        non_managed_hosts = _s[__name + '.query']('non_managed_hosts', [])
        backup_excluded.extend(
            [a for a in _s[__name + '.query']('non_managed_hosts', [])
             if a not in manual_hosts])
        bms = [a for a in db['bms']
               if a not in backup_excluded and
               get_configuration(a).get('manage_backups', True)]
        vms = [a for a in db['vms']
               if a not in backup_excluded and
               get_configuration(a).get('manage_backups', True)]
        cmap = _s[__name + '.query']('backup_configuration_map', {})
        manual_hosts = _s['mc_utils.uniquify']([
            a for a in ([a for a in cmap] + manual_hosts)
            if a not in backup_excluded and
            _s[__name + '.ip_for'](a) and  # ip is resolvable via our pillar
            a not in bms and
            a not in vms])
        # filter all baremetals and vms if they are tied to this backup
        # server
        server_conf = data.setdefault('server_conf',
                                      _s[__name + '.backup_server'](id_))
        confs = data.setdefault('confs', {})
        for host in bms + vms + manual_hosts:
            if host in backup_excluded:
                continue
            server = backup_server_for(host)
            if not server == id_:
                continue
            conf = _s[__name + '.backup_configuration_for'](host)
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
    cache_key = __name + '.backup_server_settings_for{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_top_variables(ttl=ONE_MINUTE):
    def _do_top():
        data = {}
        data.update(get_db_infrastructure_maps())
        data['non_managed_hosts'] = query('non_managed_hosts', {})
        return data
    cache_key = __name + '.get_top_variables'
    return __salt__['mc_utils.memoize_cache'](_do_top, [], {}, cache_key, ttl)


def is_dns_slave(id_, ttl=PILLAR_TTL):
    def _do(id_):
        sips = []
        nsses = __salt__[__name + '.get_nss']()
        candidates = [a for a in nsses['slaves']]
        for i in candidates[:]:
            j = nsses['map'].get(i, None)
            if j:
                candidates.append(j)
        if id_ in candidates:
            return True
        return False
    cache_key = __name + '.is_dns_slave_5{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def is_dns_master(id_, ttl=PILLAR_TTL):
    def _do(id_):
        nsses = __salt__[__name + '.get_nss']()
        candidates = [a for a in nsses['masters']]
        for i in candidates[:]:
            j = nsses['map'].get(i, None)
            if j:
                candidates.append(j)
        if id_ in candidates:
            return True
        return False
    cache_key = __name + '.is_dns_master_{0}4'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_makina_states_variables(id_, ttl=PILLAR_TTL):
    def _do(id_):
        data = {}
        data.update(get_top_variables())
        is_vm = id_ in data['vms']
        is_bm = id_ in data['bms']
        data['dns_servers'] = __salt__[__name + '.query']('dns_servers', {})
        data.update({
            'id': id_,
            'eid': id_.replace('.', '+'),
            'is_bm': is_bm,
            'is_vm': is_vm,
            'managed': (
                (is_vm or is_bm)
                and id_ not in __salt__[__name + '.query']('non_managed_hosts', {})
            ),
            'vts_sls': {'kvm': 'makina-states.kvmvm',
                        'lxc': 'makina-states.lxccontainer'},
            'bm_vts_sls': {'lxc': 'makina-states.lxc'}
        })
        data['msls'] = 'minions.{eid}'.format(**data)
        return data
    cache_key = __name + '.get_makina_states_variables_{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_supervision_conf_kind(id_, kind, ttl=PILLAR_TTL):
    def _do(id_, kind):
        rdata = {}
        supervision = __salt__[__name + '.query']('supervision_configurations', {})
        for cid, data in supervision.items():
            if data.get(kind, '') == id_:
                rdata.update(data.get('{0}_conf'.format(kind), {}))
                if 'nginx' in rdata:
                    nginx = rdata['nginx']
                    nginx = rdata.setdefault('nginx', {})
                    domain = rdata.get('nginx', {}).get('domain', id_)
                    cert, key = __salt__[
                        'mc_ssl.get_selfsigned_cert_for'](
                            domain,
                            gen=True,
                            as_text=True)[0]
                    # unknown ca signed certs do not work in nginx
                    # cert, key = __salt__['mc_ssl.ssl_certs'](domain, True)[0]
                    # nginx['ssl_cacert'] = __salt__['mc_ssl.get_cacert'](True)
                    nginx['ssl_key'] = key
                    nginx['ssl_cert'] = cert
                    nginx['ssl_redirect'] = True

        return rdata
    cache_key = __name + '.get_supervision_conf_kind{0}_{1}'.format(
        id_, kind)
    return __salt__['mc_utils.memoize_cache'](_do, [id_, kind], {}, cache_key, ttl)


def is_cloud_vm(id_, ttl=PILLAR_TTL):
    def _do(id_):
        ret = False
        maps = __salt__[__name + '.get_db_infrastructure_maps']()
        if id_ in maps['cloud_vms']:
            ret = True
        return ret
    cache_key = __name + '.is_cloud_vm{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def is_cloud_compute_node(id_, ttl=PILLAR_TTL):
    def _do(id_):
        ret = False
        maps = __salt__[__name + '.get_db_infrastructure_maps']()
        if id_ in maps['cloud_compute_nodes']:
            ret = True
        return ret
    cache_key = __name + '.is_cloud_vm{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_non_supervised_hosts(ttl=PILLAR_TTL):
    def _do():
        hosts = query('non_supervised_hosts', {})
        return hosts
    cache_key = __name + '.get_non_supervised_hosts'
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def get_supervision_objects_defs(id_):
    rdata = {}
    net = load_network_infrastructure()
    non_supervised_hosts = get_non_supervised_hosts()
    disable_common_checks = {'disk_space': False,
                             'load_avg': False,
                             'memory': False,
                             'ntp_time': False,
                             'swap': False,
                             'ping': False}
    providers = __salt__['mc_network.providers']()
    physical_hosts_to_check = set()
    host = 'HOST'
    if is_supervision_kind(id_, 'master'):
        data = __salt__[__name + '.query']('supervision_configurations', {})
        defs = data.get('definitions', {})
        sobjs = defs.setdefault('objects', OrderedDict())
        hhosts = defs.setdefault('autoconfigured_hosts', OrderedDict())
        for hhost in [a for a in hhosts if a not in non_supervised_hosts]:
            for i in ['attrs', 'services_attrs']:
                hhosts[hhost].setdefault(i, OrderedDict())
                if not isinstance(hhosts[hhost][i], dict):
                    hhosts[hhost][i] = OrderedDict()
        maps = __salt__[__name + '.get_db_infrastructure_maps']()
        for host, vts in maps['bms'].items():
            if host in non_supervised_hosts:
                continue
            physical_hosts_to_check.add(host)
            hdata = hhosts.setdefault(host, OrderedDict())
            attrs = hdata.setdefault('attrs', OrderedDict())
            sattrs = hdata.setdefault('services_attrs', OrderedDict())
            groups = attrs.setdefault('groups', [])
            parents = attrs.setdefault('parents', [])
            tipaddr = attrs.setdefault('address', ip_for(host))
            attrs.setdefault('vars.ssh_port', 22)
            attrs.setdefault('vars.snmp_port', 161)
            attrs.setdefault('vars.ssh_host', attrs['address'])
            attrs.setdefault('vars.snmp_host', attrs['address'])
            sconf = get_snmpd_conf(id_)
            p = ('makina-states.services.monitoring.'
                 'snmpd.default_')
            attrs.setdefault('vars.SNMP_PASS', sconf.get(
                p + 'password', 'secret'))
            attrs.setdefault('vars.SNMP_CRYPT', sconf.get(
                p + 'key', 'key'))
            attrs.setdefault('vars.SNMP_USER', sconf.get(
                p + 'user', 'root'))
            hdata.setdefault('raid', True)
            hdata.setdefault('inotify', True)
            hdata.setdefault('sar',
                             ['cpu', 'task', 'queueln_load',
                              'io_transfer', 'memory_stat', 'memory_util',
                              'pagestat'])
            hdata.setdefault('nic_card', ['eth0'])
            if vts:
                hdata['memory_mode'] = 'large'
            for vt in __salt__['mc_cloud_compute_node.get_all_vts']():
                attrs['vars.{0}'.format(vt)] = vt in vts
                if vt in vts:
                    for i in [
                        'HG_HYPERVISOR', 'HG_HYPERVISOR_{0}'.format(vt)
                    ]:
                        if i not in groups:
                            groups.append(i)
            # try to guess provider from name to avoid a whois lookup
            host_provider = None
            for provider in providers:
                if host.startswith(provider):
                    host_provider = provider
                    break
            if not host_provider:
                for provider in providers:
                    if __salt__[
                        'mc_network.is_{0}'.format(provider)
                    ](attrs['address']):
                        host_provider = provider
                        break
            if host_provider:
                for i in [
                    'HG_PROVIDER', 'HG_PROVIDER_{0}'.format(host_provider)
                ]:
                    if i not in groups:
                        groups.append(i)
            for i in ['HG_HOSTS', 'HG_BMS']:
                if i not in groups:
                    groups.append(i)
            if host not in __salt__[__name + '.query'](
                'non_managed_hosts', {}
            ):
                ds = hdata.setdefault('disk_space', [])
                for i in ['/', '/srv']:
                    if i not in ds:
                        ds.append(i)
            no_common_checks = hdata.get('no_common_checks', False)
            if no_common_checks:
                hdata.update(disable_common_checks)
        vm_parent = None
        if is_cloud_vm(id_):
            vm_parent = maps['vms'][id_]['target']
        for vm, vdata in maps['vms'].items():
            if vm in non_supervised_hosts:
                continue
            physical_hosts_to_check.add(host)
            vt = vdata['vt']
            host = vdata['target']
            host_ip = ip_for(host)
            hdata = hhosts.setdefault(vm, OrderedDict())
            attrs = hdata.setdefault('attrs', OrderedDict())
            sattrs = hdata.setdefault('services_attrs', OrderedDict())
            parents = attrs.setdefault('parents', [])
            tipaddr = attrs.setdefault('address', ip_for(vm))
            ssh_host = snmp_host = attrs.get('vars.ssh_host', tipaddr)
            ssh_port = attrs.get('vars.ssh_port', 22)
            snmp_port = attrs.get('vars.snmp_port', 161)
            sconf = get_snmpd_conf(id_)
            nic_cards = ['eth0']
            if vt in ['kvm', 'xen']:
                hdata.setdefault('inotify', True)
            p = ('makina-states.services.monitoring.'
                 'snmpd.default_')
            attrs.setdefault('vars.makina_host', host)
            attrs.setdefault('vars.SNMP_PASS', sconf.get(
                p + 'password', 'secret'))
            attrs.setdefault('vars.SNMP_CRYPT', sconf.get(
                p + 'key', 'key'))
            attrs.setdefault('vars.SNMP_USER', sconf.get(
                p + 'user', 'root'))
            if host not in parents:
                parents.append(host)
            # set the local ip for snmp and ssh
            if vm_parent == host:
                ssh_host = snmp_host = 'localhost'
                eext_pillar = __salt__['mc_cloud_vm.vm_extpillar'](vm)
                ssh_host = snmp_host = eext_pillar['ip']
            # we can access sshd and snpd on cloud vms
            # thx to special port mappings
            if is_cloud_vm(vm) and (vm_parent != host) and vt in ['lxc']:
                ssh_port = (
                    __salt__['mc_cloud_compute_node.get_ssh_port'](vm))
                snmp_port = (
                    __salt__['mc_cloud_compute_node.get_snmp_port'](vm))
            no_common_checks = vdata.get('no_common_checks', False)
            if tipaddr == host_ip and vt in ['lxc']:
                no_common_checks = True
            other_ips = [a.get('ip', None)
                         for a in query('cloud_vm_attrs').get(
                             vm, {}).get('additional_ips', [])
                         if a.get('ip', None)]
            if (
                tipaddr in other_ips and
                tipaddr != host_ip and
                vt in ['lxc', 'docker']
            ):
                # specific ip on lxc, monitor eth1
                nic_cards.append('eth1')
            groups = attrs.setdefault('groups', [])
            for i in ['HG_HOSTS', 'HG_VMS', 'HG_VM_{0}'.format(vt)]:
                if i not in groups:
                    groups.append(i)
            # those checks are useless on lxc
            if vt in ['lxc'] and vm in __salt__[__name + '.query']('non_managed_hosts', {}):
                no_common_checks = True
            if no_common_checks:
                hdata.update(disable_common_checks)
            attrs['vars.ssh_host'] = ssh_host
            attrs['vars.snmp_host'] = snmp_host
            attrs['vars.ssh_port'] = ssh_port
            attrs['vars.snmp_port'] = snmp_port
            hdata.setdefault('nic_card', nic_cards)

        try:
            backup_servers = query('backup_servers', {})
        except Exception:
            backup_servers = {}
        try:
            backup_excluded = query('backup_excluded', {})
        except Exception:
            backup_excluded = {}
        for host in [a for a in hhosts]:
            hdata = hhosts[host]
            if host in backup_servers:
                hdata['burp_counters'] = True
            parents = hdata.setdefault('attrs', {}).setdefault('parents', [])
            sattrs = hdata.setdefault('services_attrs', OrderedDict())
            rparents = [a for a in parents if a != id_]
            groups = hdata.get('attrs', {}).get('groups', [])
            no_common_checks = hdata.get('no_common_checks', False)
            if no_common_checks:
                hdata.update(disable_common_checks)
            for g in groups:
                if g not in sobjs:
                    sobjs[g] = {'attrs': {'display_name': g}}
                if 'HG_PROVIDER_' in g:
                    parents.append(g.replace('HG_PROVIDER_', ''))
            # try to get addr from dns
            if 'address' not in hdata['attrs']:
                socket.setdefaulttimeout(1)
                try:
                    addr = socket.gethostbyname(host)
                    # if we can determine that this entry is a vm
                    # we should disable some checks
                    # if this address is a failover
                    if rparents:
                        failover = [a
                                    for a in parents
                                    if a in net['ipsfo_map']]
                        for h in failover:
                            if addr in ips_for(h, fail_over=True):
                                hdata.update(disable_common_checks)
                                break
                    hdata['attrs']['address'] = addr
                except Exception:
                    trace = traceback.format_exc()
                    log.error('Error while determining addr for'
                              ' {0}'.format(host))
                    log.error(trace)
            # do not check dummy ip failover'ed hosts for
            # backup refreshness
            # if host not in physical_hosts_to_check:
            #    hdata['backup_burp_age'] = False
            if host in backup_excluded:
                hdata['backup_burp_age'] = False
                hdata['burp_counters'] = False
            if hdata.get('backup_burp_age', None) is not False:
                bsm = __salt__[__name + '.query']('backup_server_map', {})
                burp_default_server = bsm['default']
                burp_server = bsm.get(host, burp_default_server)
                burpattrs = sattrs.setdefault('backup_burp_age', {})
                burpattrs.setdefault('vars.ssh_host', burp_server)
                burpattrs.setdefault('vars.ssh_port', 22)
            # if id_ not in parents and id_ not in maps['vms']:
            #    parents.append(id_)
            if not hdata['attrs'].get('address'):
                try:
                    hdata['attrs']['address'] = ip_for(host)
                except Exception:
                    log.error('no address defined for {0}'.format(host))
                    hhosts.pop(host, None)
                    continue
            if id_ == host:
                for i in parents[:]:
                    parents.pop()
            hdata['parents'] = __salt__['mc_utils.uniquify'](parents)
        for g in [a for a in sobjs]:
            if 'HG_PROVIDER_' in g:
                sobjs[g.replace('HG_PROVIDER_', '')] = {
                    'type': 'Host',
                    'attrs': {
                        'import': ['HT_BASE'],
                        'groups': [g, 'HG_PROVIDER'],
                        'address': '127.0.0.1'}}
        # be sure to skip non supervised hosts
        for h in [
            hh for hh in defs['autoconfigured_hosts']
            if hh in non_supervised_hosts
        ]:
            defs['autoconfigured_hosts'].pop(h, None)
        rdata.update({'icinga2_definitions': defs})
    return rdata


def get_supervision_objects_defs_for(id_, for_):
    return get_supervision_objects_defs(id_).get(
        'icinga2_definitions', {}).get(
            'autoconfigured_hosts', {}).get(for_, {})


def get_supervision_pnp_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        k = 'makina-states.services.monitoring.pnp4nagios'
        return {k: get_supervision_conf_kind(id_, 'pnp')}
    cache_key = __name + '.get_supervision_pnp_conf{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_supervision_nagvis_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        k = 'makina-states.services.monitoring.nagvis'
        return {k: get_supervision_conf_kind(id_, 'nagvis')}
    cache_key = __name + '.get_supervision_nagvis_conf{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_supervision_ui_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        k = 'makina-states.services.monitoring.icinga_web'
        return {k: get_supervision_conf_kind(id_, 'ui')}
    cache_key = __name + '.get_supervision_ui_conf{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def is_supervision_kind(id_, kind, ttl=PILLAR_TTL):
    def _do(id_, kind):
        supervision = __salt__[__name + '.query'](
            'supervision_configurations', {})
        if not supervision:
            return False
        for cid, data in supervision.items():
            if data.get(kind, '') == id_:
                return True
        return False
    cache_key = __name + '.is_supervision_kind{0}{1}'.format(id_, kind)
    return __salt__['mc_utils.memoize_cache'](_do, [id_, kind], {}, cache_key, ttl)


def format_rrs(domain, alt=None):
    _s = __salt__
    infos = _s[__name + '.get_nss_for_zone'](domain)
    master = infos['master']
    slaves = infos['slaves']
    slave_servers = get_ns_server_slaves_for(get_servername_for(master))
    allow_transfer = []
    if slaves:
        slaveips = []
        for slv, ips in six.iteritems(slave_servers):
            for ip in ips:
                k = 'key "{0}"'.format(ip)
                if k not in slaveips:
                    slaveips.append(k)
        allow_transfer = slaveips
        soans = slaves.keys()[0]
    else:
        soans = master
    soans += "."
    if not alt:
        alt = domain
    rrs = [a.strip().replace(domain, alt)
           for a in _s[__name + '.rrs_for'](domain, aslist=True)
           if a.strip()]
    rdata = {'allow_transfer': allow_transfer,
             'serial': _s[__name + '.serial_for'](domain),
             'soa_ns': soans.replace(domain, alt),
             'soa_contact': 'postmaster.{0}.'.format(
                 domain).replace(domain, alt),
             'rrs': rrs}
    return rdata


def slave_key(id_, dnsmaster=None, master=True):
    pref = 'makina-states.services.dns.bind'
    _s = __salt__
    rdata = {}
    oip = ip_for(get_servername_for(id_), fail_over=True)
    if not master:
        if __salt__['mc_network.is_ip'](dnsmaster):
            mips = [dnsmaster]
        else:
            mips = ips_for(dnsmaster, fail_over=True)
        for mip in mips:
            # on slave side, declare the master as the tsig
            # key consumer
            rdata[pref + '.servers.{0}'.format(mip)] = {'keys': [oip]}
    # on both, say to encode with the client tsig key when daemons
    # are talking to each other
    rdata[pref + '.keys.{0}'.format(oip)] = {
        'secret': _s['mc_bind.tsig_for'](oip)}
    return rdata


def get_dns_slave_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_dns_server', True):
            return {}
        _s = __salt__
        if not _s[__name + '.is_dns_slave'](id_):
            return {}
        pref = 'makina-states.services.dns.bind'
        rdata = {pref: True, pref + '.is_slave': True}
        candidates = OrderedDict()
        domains = _s[__name + '.get_slaves_zones_for'](id_)
        candidates = []
        for domain, masterdn in domains.items():
            for ip in ips_for(masterdn, fail_over=True):
                if ip not in candidates:
                    candidates.append(ip)
            for ip in ips_for(get_servername_for(masterdn), fail_over=True):
                if ip not in candidates:
                    candidates.append(ip)
            rdata[pref + '.zones.{0}'.format(domain)] = {
                'server_type': 'slave', 'masters': candidates}
        for ip in candidates:
            rdata.update(slave_key(id_, ip, master=False))
        return rdata
    cache_key = __name + '.get_dns_slave_conf{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_ns_server_slaves_for(id_, ttl=PILLAR_TTL):
    def _do(id_):
        _s = __salt__
        candidates = OrderedDict()
        dnsslaves = _s[__name + '.get_slaves_for'](id_)['all']
        if dnsslaves:
            # slave tsig declaration
            # for each nameserver, add it's ip as a tsig candidate
            # but also register the baremetal IP as it will be the source
            # ip for network dialog
            for slv in dnsslaves:
                ips = ips_for(slv, fail_over=True)
                candidates[slv] = ips
                server = get_servername_for(slv)
                if server:
                    sips = [ip for ip in ips_for(server, fail_over=True)
                            if ip not in ips]
                    if sips:
                        candidates[server] = sips
        return candidates
    cache_key = __name + '.get_ns_server_slaves_for{0}'.format(id_)
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_dns_master_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_dns_server', True):
            return {}
        _s = __salt__
        if not _s[__name + '.is_dns_master'](id_):
            return {}
        pref = 'makina-states.services.dns.bind'
        rdata = {pref: True}
        rdata = {pref: True, pref + '.is_master': True}
        altdomains = []
        for domains in _s[__name + '.query'](
            'managed_alias_zones', {}
        ).values():
            altdomains.extend(domains)
        for domain in _s[__name + '.query']('managed_dns_zones', {}):
            if domain not in altdomains:
                rdata[pref + '.zones.{0}'.format(domain)] = _s[
                    __name + '.format_rrs'](domain)
        for domain, altdomains in six.iteritems(
            _s[__name + '.query']('managed_alias_zones', {})
        ):
            for altdomain in altdomains:
                srrs = _s[__name + '.format_rrs'](domain, alt=altdomain)
                rdata['makina-states.services.dns.bind'
                      '.zones.{0}'.format(altdomain)] = srrs
        candidates = get_ns_server_slaves_for(id_)
        tsigs = []
        for slv in candidates:
            setted_slaves = rdata.setdefault(pref + '.slaves', [])
            tsign = get_servername_for(slv)
            tip = ip_for(tsign)
            if tsign not in tsigs:
                rdata.update(slave_key(tsign))
                for ip in candidates[slv]:
                    if ip not in setted_slaves:
                        setted_slaves.append(ip)
                    rdata[pref + '.servers.{0}'.format(ip)] = {'keys': [tip]}
        return rdata
    cache_key = __name + '.get_dns_master_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def manage_network_common(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_network', True):
            return {}
        rdata = {
            'makina-states.localsettings.network.managed': True,
            'makina-states.localsettings.hostname': id_.split('.')[0]
        }
        return rdata
    cache_key = __name + '.manage_network_common{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


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
                # warning: keep ip of the hosting host
                # as the network ipv4 gw
                'route add {0} dev {1}'.format(ip_for(host), ifc),
                'route add default gw {0}'.format(ip_for(host)),
            ]
        }
    }]
    return rdata


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
        for edns in thisipifosdn:
            thisipfos.append(ipsfo[edns])
    rdata.update(manage_network_common(fqdn))
    # br0: we use br0 as main interface with by
    # defaultonly one port to escape to internet

    pref = ('makina-states.localsettings.network.'
            'ointerfaces')
    if 'br' in ifc:
        net = rdata[
            pref
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
            pref
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


def get_sysnet_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        _s = __salt__
        gconf = get_configuration(id_)
        rdata = {}
        net = _s[__name + '.load_network_infrastructure']()
        ips = net['ips']
        ipsfo = net['ipsfo']
        ipsfo_map = net['ipsfo_map']
        dbi = get_db_infrastructure_maps()
        baremetal_hosts = dbi['bms']
        mifc = gconf.get('main_network_interface', 'br0')
        if not gconf.get('manage_network', True) or not is_salt_managed(id_):
            return {}
        if id_ in baremetal_hosts:
            # always use bridge as main_if
            rdata.update(
                manage_baremetal_network(
                    id_, ipsfo, ipsfo_map, ips, ifc=mifc))
        else:
            for vt, targets in _s[__name + '.query']('vms', {}).items():
                if vt != 'kvm':
                    continue
                for target, vms in targets.items():
                    if vms is None:
                        log.error('No vms for {0}, error?'.format(target))
                    if id_ not in vms:
                        continue
                    rdata.update(
                        manage_bridged_fo_kvm_network(
                            id_, target, ipsfo, ipsfo_map, ips))
        pref = ('makina-states.localsettings.network.'
                'ointerfaces')
        net_ext_pillar = query('network_settings', {}).get(id_, {})
        if net_ext_pillar and rdata.get(pref, None):
            for i in range(len(rdata[pref])):
                for ifc in [
                    ifc for ifc in net_ext_pillar if ifc in rdata[pref][i]
                ]:
                    rdata[pref][i][ifc] = _s['mc_utils.dictupdate'](
                        rdata[pref][i][ifc], net_ext_pillar[ifc])
        return rdata
    cache_key = __name + '.get_sysnet_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_check_raid_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_check_raid', True):
            return {}
        rdata = {}
        maps = __salt__[__name + '.get_db_infrastructure_maps']()
        pref = "makina-states.localsettings.check_raid"
        if id_ in maps['bms']:
            rdata.update({pref: True})
        return rdata
    cache_key = __name + '.get_check_raid_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_supervision_client_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('supervision_client', True):
            return {}
        rdata = {}
        pref = "makina-states.services.monitoring.client"
        rdata.update({pref: True})
        return rdata
    cache_key = __name + '.get_supervision_client_conf{0}'.format(id_)+ CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_snmpd_conf(id_, ttl=60):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_snmpd', False):
            return {}
        rdata = {}
        pref = "makina-states.services.monitoring.snmpd"
        if is_salt_managed(id_):
            data = __salt__[__name + '.get_snmpd_settings'](id_)
        else:
            local_conf = __salt__['mc_macros.get_local_registry'](
                'pillar_snmpd', registry_format='pack')
            data = local_conf.setdefault(id_, {})
            data['user'] = secure_password(8)
            data['password'] = secure_password(12)
            data['key'] = secure_password(32)
            __salt__['mc_macros.update_local_registry'](
                'pillar_snmpd', local_conf, registry_format='pack')
        rdata[pref] = data.get('activated', False)
        if (
            id_ not in query('non_managed_hosts', {})
        ):
            activated = gconf.get('manage_snmpd', False)
            rdata.update({
                pref: activated,
                pref + ".default_user": data['user'],
                pref + ".default_password": data['password'],
                pref + ".default_key": data['key']})
        return rdata
    cache_key = __name + '.get_snmpd_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_backup_client_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        rdata = {}
        if not gconf.get('manage_backups', True):
            return {}
        mode = gconf.get('backup_mode', 'burp')
        if mode == 'rdiff':
            rdata['makina-states.services.backup.rdiff-backup'] = True
        elif 'burp' in mode:
            rdata['makina-states.services.backup.burp.client'] = True
        return rdata
    cache_key = __name + '.get_backup_client_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_supervision_master_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        rdata = {}
        k = 'makina-states.services.monitoring.icinga2'
        rdata[k] = get_supervision_conf_kind(id_, 'master')
        rdata['makina-states.services.monitoring.'
              'icinga2.modules.cgi.enabled'] = False
        return rdata
    cache_key = __name + '.get_supervision_master_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_supervision_confs(id_, ttl=PILLAR_TTL):
    def _do(id_):
        rdata = {}
        for kind in ['master', 'ui', 'pnp', 'nagvis']:
            if __salt__[__name + '.is_supervision_kind'](id_, kind):
                rdata.update({
                    'master': get_supervision_master_conf,
                    'ui': get_supervision_ui_conf,
                    'pnp': get_supervision_pnp_conf,
                    'nagvis': get_supervision_nagvis_conf
                }[kind](id_))
        rdata.update(
            __salt__[__name + '.get_supervision_objects_defs'](id_))
        return rdata
    cache_key = __name + '.get_supervision_confs{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_sudoers_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        rdata = {}
        pref = "makina-states.localsettings.admin.sudoers"
        if is_salt_managed(id_) and gconf.get('manage_sudoers', False):
            rdata.update({
                pref: __salt__[__name + '.get_sudoers'](id_)})
        return rdata
    cache_key = __name + '.get_sudoers_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_packages_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_packages', True):
            return {}
        msconf = __salt__[__name + '.query']('pkgmgr_conf', {})
        conf = msconf.get(id_, msconf.get('default', OrderedDict()))
        if not isinstance(conf, dict):
            conf = {}
        pref = "makina-states.localsettings.pkgs."
        rdata = OrderedDict()
        for item, val in conf.items():
            rdata[pref + item] = val
        for item, val in {
            pref + "apt.ubuntu.mirror": (
                "http://mirror.ovh.net/ftp.ubuntu.com/"),
            pref + "apt.debian.mirror": (
                "http://mirror.ovh.net/ftp.debian.org/debian/")
        }.items():
            rdata.setdefault(item, val)
        return rdata
    cache_key = __name + '.get_packages_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_shorewall_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        rdata = {}
        if not gconf.get('manage_shorewall', True):
            return {}
        rdata.update(__salt__[__name + '.get_shorewall_settings'](id_))
        return rdata
    cache_key = __name + '.get_shorewall_conf1{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_autoupgrade_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        rdata = {}
        if is_managed(id_):
            gconf = get_configuration(id_)
            rdata['makina-states.localsettings.autoupgrade'] = gconf.get(
                'manage_autoupgrades', True)
        return rdata
    cache_key = __name + '.get_autoupgrade_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def is_managed(id_, ttl=PILLAR_TTL):
    """
    Known in our infra but maybe not a salt minon
    """
    def _do(id_):
        db = get_db_infrastructure_maps()
        return id_ in db['hosts']
    cache_key = __name + '.is__managed_{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def is_salt_managed(id_, ttl=PILLAR_TTL):
    """
    Known in our infra / and also a salt minion where we expose most
    of the ext_pillars
    """
    def _do(id_):
        get_db_infrastructure_maps()
        return is_managed(id_) and id_ not in query('non_managed_hosts', {})
    cache_key = __name + '.is_salt_managed_{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_fail2ban_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_fail2ban', {}):
            return {}
        rdata = {}
        pref = "makina-states.services.firewall.fail2ban"
        rdata.update({
            pref: True,
            pref + ".ignoreip": __salt__[__name + '.whitelisted'](id_)})
        return rdata
    cache_key = __name + '.get_fail2ban_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_ntp_server_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_ntp_server', True):
            return {}
        rdata = {}
        rdata.update({
            'makina-states.services.base.ntp.kod': False,
            'makina-states.services.base.ntp.peer': False,
            'makina-states.services.base.ntp.trap': False,
            'makina-states.services.base.ntp.query': False})
        return rdata
    cache_key = __name + '.get_ntp_server_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_ldap_client_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        rdata = {}
        if is_salt_managed(id_) and gconf.get('ldap_client', False):
            conf = __salt__[__name + '.get_ldap_configuration'](id_)
            p = 'makina-states.localsettings.ldap.'
            for i in [
                'ldap_uri',
                'ldap_base',
                'ldap_passwd',
                'ldap_shadow',
                'ldap_group',
                'ldap_cacert',
                'enabled',
            ]:
                if conf.get(i):
                    rdata[p + i] = conf[i]
            for subs in ['nslcd']:
                for k in conf.get(subs, {}):
                    rdata[p + '{1}.{0}'.format(k, subs)] = conf[subs][k]
        return rdata
    cache_key = __name + '.get_ldap_client_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_mail_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_mails', True):
            return {}
        data = {}
        mail_settings = __salt__[__name + '.query'](
            'mail_configurations', {})
        mail_conf = copy.deepcopy(mail_settings.get('default', {}))
        if not mail_conf:
            return {}
        if id_ in mail_settings:
            idconf = copy.deepcopy(mail_settings[id_])
            if 'no_inherit' not in mail_conf:
                mail_conf = __salt__['mc_utils.dictupdate'](mail_conf, idconf)
            else:
                mail_conf = idconf
        dest = mail_conf['default_dest'].format(id=id_)
        data['makina-states.services.mail.postfix'] = True
        mode = 'makina-states.services.mail.postfix.mode'
        data[mode] = mail_conf.get('mode', None)
        if is_managed(id_):
            if is_salt_managed(id_) and mail_conf.get('transports'):

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
            else:
                data[mode] = 'localdeliveryonly'
            if mail_conf.get('auth', False):
                passwds = data.setdefault(
                    'makina-states.services.mail.postfix.sasl_passwd', [])
                data['makina-states.services.mail.postfix.auth'] = True
                for entry, host in mail_conf['smtp_auth'].items():
                    passwds.append({
                        'entry': '[{0}]'.format(entry),
                        'user': host['user'],
                        'password': host['password']})
            if mail_conf.get('virtual_map', None):
                vmap = data.setdefault(
                    'makina-states.services.mail.postfix.virtual_map',
                    [])
                for record in mail_conf['virtual_map']:
                    for item, val in record.items():
                        vmap.append(
                            {item.format(
                                id=id_, dest=dest): val.format(
                                    id=id_, dest=dest)})
            # proxy other keys as is
            for k in [
                a
                for a in mail_conf
                if a not in [
                    'mode',
                    'smtp_auth',
                    'auth',
                    'virtual_map',
                    'transports']
            ]:
                p = 'makina-states.services.mail.postfix.{0}'.format(k)
                data[p] = mail_conf[k]
        return data
    cache_key = __name + '.get_mail_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_ssh_keys_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_ssh_server', True):
            return {}
        rdata = {}
        pref = "makina-states.services.base.ssh.server"
        adm_pref = "makina-states.localsettings.admin.sysadmins_keys"
        a_adm_pref = "makina-states.localsettings.admin.absent_keys"
        absent_keys = []
        for k in __salt__[__name + '.get_removed_keys'](id_):
            absent_keys.append({k: {}})
        rdata.update({adm_pref: __salt__[__name + '.get_sysadmins_keys'](id_),
                      a_adm_pref: absent_keys,
                      pref + ".chroot_sftp": True})
        return rdata
    cache_key = __name + '.get_ssh_keys_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_ssh_groups_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_ssh_groups', True):
            return {}
        rdata = {}
        pref = "makina-states.services.base.ssh.server"
        rdata.update({
            pref + ".allowgroups": __salt__[__name + '.get_ssh_groups'](id_),
            pref + ".chroot_sftp": True})
        return rdata
    cache_key = __name + '.get_ssh_groups_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_etc_hosts_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_hosts', True):
            return {}
        pref = 'makina-states.localsettings.network.'
        rdata = {}
        rhosts = rdata.setdefault(pref + 'hosts_list', [])
        hosts = __salt__[__name + '.query']('hosts', {}).get(id_, [])
        if not hosts:
            hosts = []
        for entry in hosts:
            ahosts = entry['hosts']
            if isinstance(ahosts, list):
                ahosts = ' '.join(ahosts)
            ip = entry.get('ip', __salt__[__name + '.ip_for'](id_))
            rhosts.append("{0} {1}".format(ip, ahosts))
        return rdata
    cache_key = __name + '.get_etc_hosts_conf7{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_passwords_conf(id_, ttl=PILLAR_TTL):
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
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_passwords', True):
            return {}
        # load objects
        get_makina_states_variables(id_)
        rdata = {}
        pref = "makina-states.localsettings"
        apref = pref + ".admin"
        passwords = __salt__[__name + '.get_passwords'](id_)
        for user, password in passwords['crypted'].items():
            if user not in ['root', 'sysadmin']:
                rdata[
                    pref + '.users.{0}.password'.format(
                        user)] = password
        rdata.update({
            apref + ".root_password": passwords['crypted']['root'],
            apref + ".sysadmin_password": passwords['crypted']['sysadmin']})
        return rdata
    cache_key = __name + '.get_passwords_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_custom_pillar_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('custom_pillar', True):
            return {}
        rdata = {}
        rdata.update(gconf.get('custom_pillar', {}))
        return rdata
    cache_key = __name + '.get_custom_pillar_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_burp_server_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_backup_server', True):
            return {}
        rdata = {}
        if __salt__[__name + '.is_burp_server'](id_):
            conf = __salt__[__name + '.backup_server_settings_for'](id_)
            rdata['makina-states.services.backup.burp.server'] = True
            confs = __salt__[__name + '.query']('backup_server_configurations', {})
            if id_ in confs:
                for i, val in confs[id_].items():
                    rdata[
                        'makina-states.services.'
                        'backup.burp.{0}'.format(i)
                    ] = val
            for host, conf in conf['confs'].items():
                if conf['type'] in ['burp']:
                    rdata[
                        'makina-states.services.'
                        'backup.burp.clients.{0}'.format(host)
                    ] = conf['conf']
        return rdata
    cache_key = __name + '.get_burp_server_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_dhcpd_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_dhcp', True):
            return {}
        conf = __salt__[__name + '.query']('dhcpd_conf', {}).get(id_, {})
        if not conf:
            return {}
        p = 'makina-states.services.dns.dhcpd'
        return {p: conf}
    cache_key = __name + '.get_dhcpd_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_dns_resolvers(id_, ttl=PILLAR_TTL):
    def _do(id_):
        gconf = get_configuration(id_)
        if not gconf.get('manage_dns_resolvers', True):
            return {}
        rdata = {}
        db = get_db_infrastructure_maps()
        resolvers = set()
        search = set()
        if id_ in db['vms']:
            vm_ = db['vms'][id_]
            if vm_.get('vt', '') in ['lxc']:
                resolvers.add('10.5.0.1')
            resolvers.add(ip_for(db['vms'][id_]['target']))
        conf = __salt__[__name + '.query']('dns_resolvers', {})
        sconf = __salt__[__name + '.query']('dns_search', {})
        conf = conf.get(id_, conf.get('default', []))
        sconf = sconf.get(id_, sconf.get('default', []))
        if not isinstance(conf, list):
            conf = []
        if not isinstance(sconf, list):
            sconf = []
        for i in conf:
            resolvers.add(i)
        for i in sconf:
            search.add(i)
        p = 'makina-states.localsettings.dns.'
        rdata[p[:-1]] = True
        if search:
            rdata[p + 'search'] = [a.strip() for a in search if a.strip()]
        if resolvers:
            rdata[p + 'default_dnses'] = [a.strip()
                                          for a in resolvers if a.strip()]
        return rdata
    cache_key = __name + '.get_dns_resolvers{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_ssh_hosts(ttl=PILLAR_TTL):
    def _do():
        try:
            ssh_hosts = copy.deepcopy(query('ssh_hosts'))
        except NoResultError:
            log.info('No ssh_hosts section in configuration')
            ssh_hosts = {}
        return ssh_hosts
    cache_key = __name + '.get_ssh_hosts' + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def get_ssh_connection_infos(id_, ttl=PILLAR_TTL):
    def _do():
        _s = __salt__
        infos = _s['mc_cloud.ssh_host_settings'](id_)
        return {saltapi.SSH_CON_PREFIX: infos}
    cache_key = __name + '.get_ssh_connection_infos{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def get_masterless_makinastates_hosts(ttl=PILLAR_TTL):
    '''
    Expose on salt metadatas on how to connect
    on each part of the infra using ssh
    '''
    _o = __opts__
    _s = __salt__
    def _do():
        data = set()
        try:
            db = _s['mc_pillar.get_db_infrastructure_maps']()
            for kind in ('bms', 'vms'):
                for id_, idata in six.iteritems(db[kind]):
                    data.add(id_)
            return list(data)
        except DatabaseNotFound:
            log.debug('mc_pillar is not configured')
            return []
    cache_key = __name + '.get_masterless_makinastates_hosts' + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def get_masterless_makinastates_hosts_conf(ttl=PILLAR_TTL):
    _o = __opts__
    _s = __salt__
    controller = _s['mc_cloud.is_a_controller'](_o['id'])
    if not controller:
        return {}
    pref = 'makina-states.cloud.masterless_hosts'
    return {pref: get_masterless_makinastates_hosts()}


def get_db_md5(ttl=10):
    def _do():
        with open(get_db()) as fic:
            nmd5 = hashlib.md5(fic.read()).hexdigest()
        return nmd5
    cache_key = __name + '.get_db_md5' + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def invalidate_mc_pillar():
    '''
    if the db changed, invalidate the cache
    '''
    try:
        md5 = get_db_md5()
        lc = __salt__['mc_utils.get_local_cache']()
        mc = __salt__['mc_utils.get_mc_server']()
        invalidate = __salt__['mc_utils.invalidate_memoize_cache']
        omd5 = lc.get('mc_pillar_db_md5', md5)
        if omd5 != md5:
            log.info('mc_pillar: DB changed,'
                     ' invalidating local cache')
            for k in [a for a in mc_states.api._CACHE_KEYS]:
                fun = mc_states.api._CACHE_KEYS[k][2]
                if fun.startswith('mc_pillar'):
                    invalidate(k, caches=[lc, _cache])
        if mc is not None:
            r = __opts__['pillar_roots']['base'][0]
            k = r + '_mc_pillar_db_md5'
            try:
                momd5 = mc[k]
            except (KeyError, IndexError):
                momd5 = mc[k] = md5
            if momd5 != md5:
                log.error('{0} {1}'.format(momd5, md5))
                log.info('mc_pillar: DB changed,'
                         ' invalidating whole memcached cache')
                invalidate('all', memcache=mc)
                mc[k] = md5
        # normally this cache is already empty, but in case.
        for k in [a for a in _cache]:
            _cache.pop(k, None)
    except IOError:
        pass
    except Exception:
        log.error(traceback.format_exc())


def json_pillars(id_, pillar=None, raise_error=True, *args, **kw):
    _s = __salt__
    dirs = _s['mc_macros.get_pillar_dss']([id_])
    data = OrderedDict()
    # do not load cache pillar on controller, we will rely here on
    # mc_pillar and other ext_pillars directly
    if has_db():
        return data
    for section in ['*', id_]:
        if section not in dirs:
            continue
        for pdir in dirs[section]:
            if not os.path.exists(pdir):
                continue
            for i in [a
                      for a in os.listdir(pdir)
                      if a.endswith('.json')]:
                try:
                    pf = os.path.join(pdir, i)
                    with open(pf) as fic:
                        data = _s['mc_utils.dictupdate'](
                            data, json.loads(fic.read()))
                except (IOError, ValueError):
                    pass
    return data


def ext_pillar(id_, pillar=None, raise_error=True, *args, **kw):
    _s = __salt__
    invalidate_mc_pillar()
    if pillar is None:
        pillar = OrderedDict()
    if not has_db():
        dbpath = get_db()
        msg = (
            'MC_PILLAR not loader:\n'
            'DATABASE DOES NOT EXISTS: ' + dbpath
        ).replace('.json', '.{json,sls,yaml}')
        if 'salt' in dbpath:
            log.error(msg)
        return {}
    if isinstance(kw, dict):
        profile_enabled = kw.get('profile', False)
    # profile_enabled = True
    data = {}
    if profile_enabled:
        pr = cProfile.Profile()
        pr.enable()

    dictupdate = _s['mc_utils.dictupdate']
    for i in [
        # catch mc_pillar.& & <foo>.*pillar.*
        '.*(ext)*_?pillar.*',
        'mc_cloud.*(get_cloud_conf|get_vms)'
    ]:
        __salt__['mc_utils.register_memcache_first'](i)

    is_this_salt_managed = is_salt_managed(id_)
    is_this_managed = is_managed(id_)
    raise_error = []
    for callback, copts in {
        'mc_env.ext_pillar': {'only_managed': False},
        __name + '.get_snmpd_conf': {'only_known': False},
        __name + '.get_custom_pillar_conf': {'only_managed': False},
        __name + '.get_dhcpd_conf': {'only_managed': False},
        __name + '.get_etc_hosts_conf': {'only_managed': False},
        __name + '.get_packages_conf': {'only_managed': False},
        __name + '.get_autoupgrade_conf': {'only_managed': False},
        __name + '.get_backup_client_conf': {},
        __name + '.get_dns_resolvers': {},
        __name + '.get_mail_conf': {},
        __name + '.get_firewalld_conf': {},
        __name + '.get_ms_iptables_conf': {},
        __name + '.get_shorewall_conf': {},
        __name + '.get_burp_server_conf': {},
        __name + '.get_check_raid_conf': {},
        __name + '.get_ssh_connection_infos': {},
        __name + '.get_dns_master_conf': {},
        __name + '.get_dns_slave_conf': {},
        __name + '.get_exposed_global_conf': {},
        __name + '.get_fail2ban_conf': {},
        __name + '.get_ldap_client_conf': {},
        __name + '.get_ntp_server_conf': {},
        __name + '.get_passwords_conf': {},
        __name + '.get_slapd_conf': {},
        __name + '.get_masterless_makinastates_hosts_conf': {},
        __name + '.get_ssh_groups_conf': {},
        __name + '.get_ssh_keys_conf': {},
        __name + '.get_ssl_conf': {},
        __name + '.get_sudoers_conf': {},
        __name + '.get_supervision_client_conf': {},
        __name + '.get_supervision_confs': {},
        __name + '.get_sysnet_conf': {},
        'mc_cloud.ext_pillar': {},
    }.items():
        try:
            if '.' not in callback:
                callback = __name + '.{0}'.format(callback)
            # CONDITIONNAL PILLAR EXPOSURE
            #
            # if minion is not a minion managed via ext pillar
            # and we did not force this specific ext pillar function
            # if force execution for those minions
            # known from the database but not managed via extpillar
            # and minion is known, force execution
            skip = True
            if is_this_salt_managed:
                skip = False
            else:
                if not copts.get('only_managed', True):
                    skip = False
                if is_this_managed and not copts.get('only_known', True):
                    skip = False
            if skip:
                continue
            # log.error(callback)
            # only dictupdate if there is key overlay
            subpillar = _s[callback](id_)
            data = dictupdate(data, subpillar)
        except Exception, ex:
            trace = traceback.format_exc()
            msg = 'ERROR in mc_pillar: {0}/{1}'.format(callback, id_)
            raise_error.append(msg)
            log.error(msg)
            log.error(ex)
            log.error(trace)
    if profile_enabled:
        pr.disable()
        if not os.path.isdir('/tmp/stats'):
            os.makedirs('/tmp/stats')
        date = datetime.datetime.now().isoformat()
        ficp = '/tmp/stats/{0}.{1}.pstats'.format(id_, date)
        fico = '/tmp/stats/{0}.{1}.dot'.format(id_, date)
        ficn = '/tmp/stats/{0}.{1}.stats'.format(id_, date)
        if not os.path.exists(ficp):
            pr.dump_stats(ficp)
            with open(ficn, 'w') as fic:
                pstats.Stats(pr, stream=fic).sort_stats('cumulative')
        msr = __salt__['mc_locations.msr']()
        __salt__['cmd.run'](
            msr + '/bin/pyprof2calltree '
            '-i "{0}" -o "{1}"'.format(ficp, fico), python_shell=True)
    if raise_error:
        raise PillarError('\n    '+'\n    '.join(raise_error))
    return data


def get_exposed_global_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        p = 'makina-states.pillar.gconf'
        exdata = {}
        gconf = get_configuration(id_)
        if not gconf.get('manage_exposed_glocal_conf', True):
            return {}
        exdata = {p: copy.deepcopy(gconf)}
        return exdata
    cache_key = __name + '.get_exposed_global_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_global_conf(section, entry=10, ttl=PILLAR_TTL):
    def _do(section, entry):
        _s = __salt__
        extdata = copy.deepcopy(
            _s[__name + '.query'](section, {}).get(entry))
        if not extdata:
            if entry not in ['default']:
                log.debug('No {0} section in global cloud conf:'
                          ' {1}'.format(entry, section))
            extdata = {}
        return extdata
    cache_key = __name + '.get_global_conf{0}{1}'.format(section, entry) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](
        _do, [section, entry], {}, cache_key, ttl)


def get_domains_for(id_, ttl=PILLAR_TTL):
    def _do(id_):
        _s = __salt__
        gconf = get_configuration(id_)
        domains = [id_]
        domains += [a for a in gconf.get('domains', [])]
        cn_attrs = _s[__name + '.query']('cloud_cn_attrs', {})
        vm_attrs = _s[__name + '.query']('cloud_vm_attrs', {})
        cloud = get_cloud_conf()
        vms = []
        if id_ in cloud['vms'].keys():
            vms.append(id_)
        if id_ in cloud['cns'].keys():
            domains += [a for a in cn_attrs.get(id_, {}).get('domains', [])]
            for vm in cloud['cns'][id_]['vms']:
                vms.append(vm)
        for vm in vms:
            domains.append(vm)
            domains += [a for a in vm_attrs.get(vm, {}).get('domains', [])]
        # tie extra domains of vms to a A record: part2
        domains = _s['mc_utils.uniquify'](domains)
        return domains
    cache_key = __name + '.get_domains_for{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def add_ssl_cert(common_name, cert_content, cert_key, data=None):
    if not isinstance(data, dict):
        data = {}
    p = 'makina-states.localsettings.ssl.'
    data[p + 'certificates.' + common_name] = [cert_content, cert_key]
    return data


def get_ssl_certs():
    _s = __salt__
    ckey = 'mc_pillar.get_ssls_certs'
    confcerts = query('ssl_certs', {})
    certs = _cache.setdefault(ckey, {})
    if not certs:
        for id_, certdata in six.iteritems(confcerts):
            try:
                infos = _s['mc_ssl.get_cert_infos'](certdata[0], certdata[1])
                for id__ in [id_, infos['cn']] + infos['altnames']:
                    certs[id__] = infos
            except (Exception,) as exc:
                log.error('{0} ssl cert had an error while loading')
                log.error('{0}'.format(exc))
    return certs


def get_cert_data(cn):
    _s = __salt__
    certs = get_ssl_certs()
    # if cn is explicitly defined in database, use that
    # else try to use a wildcard domain over a normal domain
    # unless this one has an entry in which case we will try to get both
    wd = _s['mc_ssl.get_wildcard'](cn)
    if wd:
        if cn not in certs:
            cn = wd
    if cn in certs:
        certdata = certs[cn]
    else:
        cert, key = _s['mc_ssl.get_selfsigned_cert_for'](cn, gen=True)
        certdata = certs[cn] = _s['mc_ssl.get_cert_infos'](cert, key)
    return certdata


def get_ssl_conf(id_, ttl=PILLAR_TTL):
    def _do(id_):
        _s = __salt__
        gconf = get_configuration(id_)
        if not gconf.get('manage_ssl', True):
            return {}
        rdata = OrderedDict()
        confs = query('ssl', {})
        certs = get_ssl_certs()
        # load also a selfsigned wildcard
        # certificate for all of those domains
        todo = _s['mc_utils.uniquify'](
            (confs.get(id_,
                       confs.get('default', [])) +
                get_domains_for(id_)))
        this_cert, this_wcert = id_, _s['mc_ssl.get_wildcard'](id_)
        todo = [a for a in todo if a not in [this_cert, this_wcert]]
        certdatas = OrderedDict()
        # for the machine fqdn related certificate, we will
        # try to use a wildcard cert over an exact one
        machine_cn, machine_cert = None, None
        for cn in this_wcert, this_cert:
            machine_cn, machine_cert = cn, certs.get(cn, None)
            if machine_cert:
                break
        if not machine_cert:
            machine_cn, machine_cert = this_wcert, get_cert_data(this_wcert)
        certdatas[machine_cn] = machine_cert
        # for all other domain,
        # if we dont find a matching certificate
        # try to find a certificate on the wildcarded domain
        # else
        #   generate & use a selfsigned certificate on the wildcard domain
        for cn in todo:
            certdatas[cn] = get_cert_data(cn)
        for cn, cdata in six.iteritems(certdatas):
            add_ssl_cert(
                cdata['cn'], cdata['cert'], cdata['cert_data'][1], rdata)
        return rdata
    cache_key = __name + '.get_ssl_conf{0}'.format(id_) + CACHE_INC_TOKEN
    return __salt__['mc_utils.memoize_cache'](_do, [id_], {}, cache_key, ttl)


def get_masterless_makinastates_groups(host, pillar=None):
    if pillar is None:
        pillar = {}
    groups = set()
    mysql = re.compile('mysql', flags=rei_flags)
    pgsql = re.compile('osm|pgsql|postgresql', flags=rei_flags)
    es = re.compile('es|elaticsearch', flags=rei_flags)
    mongo = re.compile('mongo', flags=rei_flags)
    rabbit = re.compile('rabbit', flags=rei_flags)
    solr = re.compile('solr', flags=rei_flags)
    prod = re.compile('^prod-', flags=rei_flags)
    dev = re.compile('^dev-', flags=rei_flags)
    staging = re.compile('^staging-', flags=rei_flags)
    qa = re.compile('^qa-', flags=rei_flags)
    what = {'all': True,
            'mysql': mysql.search(host),
            'pgsql': pgsql.search(host),
            'rabbit': rabbit.search(host),
            'solr': solr.search(host),
            'es': es.search(host),
            'mongo': mongo.search(host),
            'prod': prod.search(host),
            'staging': staging.search(host),
            'qa': qa.search(host),
            'dev': dev.search(host)}
    for group, test in six.iteritems(what):
        if test:
            groups.add(group)
    is_ = pillar.get('makina-states.cloud', {}).get('is', {})
    mpref = 'makina-states.services.backup.burp.server'
    if pillar.get(mpref, False):
        groups.add('burp_servers')
    mpref = 'makina-states.services.dns.bind.is_master'
    if pillar.get(mpref, False):
        groups.add('dns_masters')
    mpref = 'makina-states.services.dns.bind.is_slave'
    if pillar.get(mpref, False):
        groups.add('dns_slaves')
    if True in [('dns.bind.servers' in a) for a in pillar]:
        groups.add('dns')
    if is_.get('vm', True):
        groups.add('vms')
    if is_.get('compute_node', True):
        groups.add('bms')
    if is_.get('controller', True):
        groups.add('controllers')
    return groups

def test():
    return True


def loaded():
    stack = inspect.stack()
    fun_names = [n[3] for n in stack]
    try:
        ret = __pillar__.get(__name + '.loaded', False)
        if ret and (
            True in [(
                ('extpillar' in a) or
                ('ext_pillar' in a)
            ) for a in fun_names]
        ):
            ret = False
        if ret and not has_db():
            ret = False
    except Exception:
        ret = Falss
    return ret
