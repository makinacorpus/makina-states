# -*- coding: utf-8 -*-
'''
.. _module_mc_dns:

mc_dns / dns settings
=======================


The main settings in there is "default_dnses" which are the dns for resolution
As soon as you install a dns service on the behalf of makina-states

'''

import logging
from mc_states import api
from mc_states.grains import makina_grains
import dns
import dns.query
import dns.message
import dns.rdatatype
six = api.six


log = logging.getLogger(__name__)


def test_ns(ns):
    ret = False
    try:
        request = dns.message.make_query('fr', dns.rdatatype.NS)
        res = dns.query.tcp(request, ns, timeout=5)
        if res.rcode() == 0:
            ret = ns
    except Exception:
        pass
    return ret


def gateway_ns():
    # try to default nameserver to the default gateway addr
    ns = None
    routes, route, gw = makina_grains._routes()
    if test_ns(gw):
        ns = gw
    return ns


def _sort_ns(google_first=False):
    def __sort_ns(ns):
        pref = "a"
        if google_first:
            lpref = 'u'
            gpref = 'm'
        else:
            gpref = 'u'
            lpref = 'm'
        if ns in ['8.8.8.8']:
            pref = gpref + "1"
        if ns in ['4.4.4.4']:
            pref = gpref + "2"
        elif ns in ['127.0.1.1']:
            pref = 'z'
        elif ns in ['127.0.0.1']:
            pref = lpref
        return '{0}_{1}'.format(pref, ns)
    return __sort_ns


def settings(ttl=15*60):

    def _do():
        settings = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.dns', {
                'no_default_dnses': False,
                'google_first': False,
                'search': [],
                'default_dnses': []})
        if settings['default_dnses']:
            # if we have an explicit ns, dont check localhost as we
            # are certainly in a container without a local ns, just
            # skip it. If we have only one ns, we will hit it anyway
            # in case of google failure at it will be the third
            # and the last NS.
            settings['google_first'] = True
        if not settings['no_default_dnses']:
            nss = [a
                   for a in ([gateway_ns()] +
                             ['127.0.0.1', '127.0.1.1', '8.8.8.8'])
                   if a]
            for i in nss:
                if i not in settings['default_dnses']:
                    settings['default_dnses'].append(i)
        settings['default_dnses'] = __salt__['mc_utils.uniquify'](
            settings['default_dnses'])
        settings['default_dnses'].sort(key=_sort_ns(settings['google_first']))
        return settings
    cache_key = 'mc_dns.settings'
    return __salt__['mc_utils.memoize_cache'](_do, [], {}, cache_key, ttl)
