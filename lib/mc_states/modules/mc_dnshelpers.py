#!/usr/bin/env python
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

'''
.. _module_mc_dnshelpers:

mc_dnshelpers
=======================

The functions else of settings Must be executed on dns master side

This needs those extra pillar settings to configure
mc_provider (api settings)


'''

import pprint
import logging
import traceback
import copy
from salt.utils.odict import OrderedDict
from mc_states import api
six = api.six


# try:
#     from suds.xsd.doctor import ImportDoctor, Import
#     from suds.client import Client
#     HAS_SUDS = True
# except ImportError:
#     HAS_SUDS = False

try:
    import whois
    HAS_PYWHOIS = True
except ImportError:
    HAS_PYWHOIS = False

try:
    import ovh
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


log = logging.getLogger(__name__)


def ip_for(*a, **kw):
    return __salt__['mc_pillar.ip_for'](*a, **kw)


def ips_for(*a, **kw):
    return __salt__['mc_pillar.ips_for'](*a, **kw)


def settings(ttl=15*60):
    '''
    Share the mc_dns.settings for shortness of configuration items
    '''
    def _do():
        settings = __salt__['mc_utils.defaults'](
            'makina-states.dns', {})
        return settings
    cache_key = 'mc_dnshelpers.settings'
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)


def register_checks():
    if not __context__.get('mc_dns._register_checks',  False):
        if not HAS_OVH:
            raise ValueError('no ovh')
        if not HAS_PYWHOIS:
            raise ValueError('no pywhois')
        __context__.get('mc_dns._register_checks',  True)


def gandi_glues(domain, dnss):
    register_checks()
    _s = __salt__
    api, apikey = _s['mc_provider.gandi_client'](domain=domain)
    current_glues = api.domain.host.list(apikey, domain)
    ret = OrderedDict()
    ret['add'] = OrderedDict()
    ret['update'] = OrderedDict()
    ret['delete'] = OrderedDict()
    ret['ns'] = OrderedDict()
    toadd = {}
    toupdate = {}
    todelete = {}
    for a in current_glues:
        if a['name'] not in dnss:
            ips = todelete.setdefault(a['name'], [])
            for ip in a['ips']:
                if ip not in ips:
                    ips.append(ip)
    for a in current_glues:
        if a['name'] in dnss:
            aips = dnss[a['name']][:]
            aips.sort()
            bips = a['ips'][:]
            bips.sort()
            if aips != bips:
                toupdate[a['name']] = aips
    for dns in dnss:
        if dns not in [a['name'] for a in current_glues]:
            toadd[dns] = dnss[dns][:]
    error = False
    for ns, ips in six.iteritems(toadd):
        try:
            ret['add'][ns] = api.domain.host.create(apikey, ns, ips)
            assert ret['add'][ns]['errortype'] is None
        except KeyboardInterrupt:
            raise
        except Exception:
            print(traceback.format_exc())
            error = True
    if not error:
        for ns, ips in six.iteritems(toupdate):
            try:
                ret['update'][ns] = api.domain.host.update(apikey, ns, ips)
                assert ret['update'][ns]['errortype'] is None
            except KeyboardInterrupt:
                raise
            except Exception:
                print(traceback.format_exc())
                error = True
    if not error:
        try:
            ret['ns'] = api.domain.nameservers.set(
                apikey, domain, [a for a in dnss])
            assert ret['ns']['errortype'] is None
        except KeyboardInterrupt:
            raise
        except Exception:
            print(traceback.format_exc())
            error = True
    if not error:
        for ns, ips in six.iteritems(todelete):
            try:
                ret['delete'][ns] = api.domain.host.delete(apikey, ns)
                assert ret['delete'][ns]['errortype'] is None
            except KeyboardInterrupt:
                raise
            except Exception:
                print(traceback.format_exc())
                error = True
    ret['error'] = error
    return ret


def gandi_set_nss(domain, dnss):
    register_checks()
    log.info('{0}: Setting up DNS'.format(domain))
    api, apikey = __salt__['mc_provider.gandi_client'](domain=domain)
    ret = OrderedDict()
    error = False
    try:
        ret['set'] = api.domain.nameservers.set(
            apikey, domain, [a for a in dnss])
        assert ret['set']['errortype'] is None
    except KeyboardInterrupt:
        raise
    except Exception:
        print(traceback.format_exc())
        error = True
    ret['error'] = error
    return ret


def ovh_set_nss(domain, dnss, dnssec=False):
    register_checks()
    log.info('{0}: Setting up DNS'.format(domain))
    if not dnss:
        raise ValueError('no dns for {0}'.format(domain))
    _s = __salt__
    crets = OrderedDict()
    client = __salt__['mc_provider.ovh_client'](domain=domain)
    dnssec_ep = '/domain/zone/{0}/dnssec'.format(domain)
    dnssec_status = client.get(dnssec_ep)['status'] != 'disabled'
    if dnssec:
        if not dnssec_status:
            client.post(dnssec_ep)
            log.info('{1}: activated dnssec')
    else:
        if dnssec_status:
            client.delete(dnssec_ep)
            log.info('{1}: deactivated dnssec')
    hosted_status = client.get('/domain/{0}'.format(domain))
    if hosted_status['nameServerType'] == 'hosted':
        client.put('/domain/{0}'.format(domain), nameServerType='external')
    current_nss = {}
    todelete = set()
    skip = []
    crets['skipped'] = OrderedDict()
    for nsid in client.get(
        '/domain/{0}/nameServer'.format(domain)
    ):
        ns = client.get('/domain/{0}/nameServer/{1}'.format(
            domain, nsid))
        host = ns['host']
        dns = current_nss.setdefault(host, {})
        cns = current_nss[host] = __salt__['mc_utils.dictupdate'](dns, ns)
        if host not in dnss:
            todelete.add(nsid)
        if host in dnss and cns['ip']:
            if cns['ip'] == dnss[host][0]:
                crets['skipped'][host] = cns
                skip.append(host)
            else:
                todelete.add(nsid)

    def remove_remaining(remaining, log=False):
        can_delete = True
        for ns in [a for a in todelete]:
            if not can_delete:
                continue
            ret = client.get('/domain/{0}/nameServer/{1}'.format(domain, ns))
            if ret['toDelete']:
                continue
            try:
                client.delete('/domain/{0}/nameServer/{1}'.format(domain, ns))
                log.info('{1}: deleted ns: {0}'.format(ns, domain))
                todelete.remove(ns)
            except (Exception,) as exc:
                if log:
                    print(exc)
                    log.error(traceback.format_exc())
                can_delete = False
                continue
        return todelete
    todelete = remove_remaining(todelete)
    for ns, data in six.iteritems(dnss):
        if ns in skip:
            continue
        nameservers = [{'host': ns, 'ip': a} for a in data]
        crets['ns_{0}'.format(ns)] = ret = client.post(
            '/domain/{0}/nameServer'.format(domain), nameServer=nameservers)
        if ret['status'] != 'todo':
            log.error("{0} unexpected result".format(ns))
            log.error(pprint.pformat(ret))
        else:
            log.info('{1}: Created ns: {0}'.format(ns, domain))
        # try to delete remaining deleted servers
        todelete = remove_remaining(todelete)
    todelete = remove_remaining(todelete, log=True)
    if todelete:
        log.error('{0}: {1} were not deleted'.format(ns, todelete))
    return crets


def get_gandi_handled_domains(domain=None, ttl=300):
    register_checks()

    def _do(domain):
        api, apikey = __salt__['mc_provider.gandi_client'](domain=domain)
        return sorted(__salt__['mc_utils.uniquify'](
            [a['fqdn'] for a in api.domain.list(apikey)]))
    cache_key = 'mc_dns.get_gandi_handled_domains{0}'.format(domain)
    return __salt__['mc_utils.memoize_cache'](_do, [domain], {}, cache_key, ttl)


def get_ovh_handled_domains(domain=None, ttl=300):
    register_checks()

    def _do(domain):
        client = __salt__['mc_provider.ovh_client'](domain=domain)
        return sorted(client.get('/domain'))
    cache_key = 'mc_dns.get_ovh_handled_domains{0}'.format(domain)
    return __salt__['mc_utils.memoize_cache'](_do, [domain], {}, cache_key, ttl)


def domain_registrar(domain):
    register_checks()
    providers = ['gandi', 'ovh']
    # prefer rely on API
    for i in providers:
        if not __salt__[
            'mc_provider.get_{0}_opt'.format(i)
        ]('activated', domain=domain):
            continue
        names = __salt__['mc_dns.get_{0}_handled_domains'.format(i)]()
        if domain in names:
            return i
    # fallback on whois
    return __salt__['mc_network.domain_registrar'](domain)


def register_dns_masters(only_domains=None, only_providers=None):
    '''
    Use registrar apis to switch the nameservers to the ones
    we manage on salt

    only_domains
        list of domains to act on, if empty all managed domains
        will be checked

    only_providers
        limit action to one or more providers  (gandi, ovh)

    CLI Examples::

        salt-call mc_dns.register_dns_masters only_providers=ovh
        salt-call mc_dns.register_dns_masters only_providers=gandi
        salt-call mc_dns.register_dns_masters foo.net

    '''
    register_checks()
    _s = __salt__
    if isinstance(only_providers, six.string_types):
        only_providers = only_providers.split(',')
    if isinstance(only_domains, six.string_types):
        only_domains = only_domains.split(',')
    if not only_domains:
        only_domains = []
    managed_domains = _s['mc_pillar.query']('managed_dns_zones')[:]
    if not only_domains:
        only_domains = managed_domains
    errors = [a for a in only_domains if a not in managed_domains]
    if errors:
        raise ValueError('{0} are not managed'.format(errors))
    dnss = {}
    for i in _s['mc_pillar.get_nss']()['slaves']:
        dnss[i] = ips_for(i, fail_over=True)
    # for each name server, registrer its glue record
    # in the domain it belongs
    glues = {}
    crets = OrderedDict()
    crets['set_ns'] = OrderedDict()
    for dns in dnss:
        domain = '.'.join(dns.split('.')[-2:])
        glues.setdefault(domain, {})
        glues[domain][dns] = dnss[dns]
    try:
        skipped = _s['mc_pillar.query']('skipped_updated_domains')
    except Exception:
        skipped = []
    for domain, dnss in six.iteritems(glues):
        provider = domain_registrar(domain)
        fun = 'mc_dns.{0}_glues'.format(provider)
        if fun not in _s:
            log.error(
                'Registrar {0} switcher doest exist'
                ' for {1}'.format(fun, domain))
            continue
        if not _s[
            'mc_provider.get_{0}_opt'.format(provider)
        ]('activated', domain=domain):
            log.error('{0} not configured'.format(provider))
            continue
        crets['glues'] = _s[fun](domain, dnss)
    for domain in only_domains:
        if domain in skipped:
            log.error('{0} SKIPPED'.format(domain))
            continue
        provider = domain_registrar(domain)
        fun = 'mc_dns.{0}_set_nss'.format(provider)
        if not _s[
            'mc_provider.get_{0}_opt'.format(provider)
        ]('activated', domain=domain):
            log.error('{0} not configured'.format(provider))
            continue
        if fun not in _s:
            log.error(
                'Registrar {0} switcher doest exist'
                ' for {1}'.format(fun, domain))
            continue
        if only_providers:
            if provider not in only_providers:
                continue
        crets['set_ns'][domain] = _s[fun](domain, dnss)
    return crets
# vim:set et sts=4 ts=4 tw=80:
