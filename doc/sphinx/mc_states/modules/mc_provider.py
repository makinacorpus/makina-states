#!/usr/bin/env python
'''

.. _module_mc_provider:

mc_provider / provider functions
============================================



Useful functions to locate a particular host
or setting
'''

# -*- coding: utf-8 -*-
# Import python libs
import xmlrpclib
import logging
import urllib2
import requests
import mc_states.api
from salt.utils.odict import OrderedDict

import salt.exceptions

class ClientNotActivated(salt.exceptions.SaltException):
    """."""

__name = 'provider'
_marker = object()

log = logging.getLogger(__name__)

try:
    import ovh
    HAS_OVH = True
except ImportError:
    HAS_OVH = False


def settings():
    '''
    provider settings

        is
            booleans

            online
                are we on an online host
            ovh
                are we on an ovh host
            sys
                are we on an soyoustart host

        have_rpn
            online specific: do we have rpn

    '''
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        grains = __grains__
        is_ovh = 'ovh' in __grains__['id']
        is_sys = __grains__['id'].startswith('sys-')
        is_online = 'online-dc' in __grains__['id']
        have_rpn = None
        ifaces = grains['ip_interfaces'].items()
        data = __salt__['mc_utils.defaults'](
            'makina-states.localsettings.provider', {
                'gandi': {
                    'default': {
                        'activated': False,
                        'api': 'https://rpc.gandi.net/xmlrpc/',
                        'api_key': None,
                    }
                },
                'ovh': {
                    'default': {
                        'activated': False,
                        'api': 'https://eu.api.ovh.com/1.0',
                        'endpoint': 'ovh-eu',
                        'login': None,
                        'password': None,
                        'application_name': None,
                        'application_description': None,
                        'application_key': None,
                        'application_secret': None,
                        'consumer_key': None,
                    }
                },
                'is': {
                    'online': is_online,
                    'ovh': is_ovh,
                    'sys': is_sys,
                },
                'have_rpn': have_rpn,
            })
        if data['is']['online'] and data['have_rpn'] is None:
            for ifc in ['eth1', 'em1']:
                if True in [ifc == a[0] for a in ifaces]:
                    data['have_rpn'] = True  # must stay none if not found
        return data
    return _settings()


def get_provider_opt(provider, opt, default=_marker, domain=None):
    data = settings()[provider]
    val = _marker
    if domain:
        val = data.get(domain, {}).get(opt, _marker)
    if val is _marker:
        val = data['default'].get(opt, _marker)
    if val is _marker:
        if default is not _marker:
            val = default
        else:
            raise KeyError(opt)
    return val


def get_ovh_opt(opt, default=None, domain=None):
    return get_provider_opt('ovh', opt, domain=domain)


def get_gandi_opt(opt, default=None, domain=None):
    return get_provider_opt('gandi', opt, domain=domain)


def ovh_auth(app_key=None):
    if not app_key:
        app_key = get_ovh_opt('application_key')
    headers = {"X-Ovh-Application": app_key,
               "Content-type": "application/json"}
    end_point = get_ovh_opt('api') + '/auth/credential'
    payload = __salt__['mc_utils.json_dump']({
        "accessRules": [
            {"method": "POST", "path": "/*"},
            {"method": "GET", "path": "/*"},
            {"method": "PUT", "path": "/*"},
            {"method": "DELETE", "path": "/*"}
        ],
        "redirection": "https://www.makina-corpus.com",
    })
    try:
        res = requests.post(end_point, data=payload, headers=headers)
        data = res.json()
    except (urllib2.HTTPError,) as exc:
        if exc.getcode() == 404:
            raise Exception('register a new app on'
                            ' https://eu.api.ovh.com/createApp/')
    return data


def gandi_client(**kw):
    domain = kw.get('domain', None)
    if not get_gandi_opt('activated', domain=domain):
        raise ClientNotActivated('gandi')
    uapi = get_gandi_opt('api', domain=domain)
    apikey = get_gandi_opt('api_key', domain=domain)
    api = xmlrpclib.ServerProxy(uapi)
    return api, apikey


def ovh_client(**kw):
    domain = kw.pop('domain', None)
    if not get_ovh_opt('activated', domain=domain):
        raise ClientNotActivated('ovh')
    if not HAS_OVH:
        raise ValueError(
            'Please install ovh bindings, pip install ovh')
    ckw = {}
    for i in [
        'application_key',
        'endpoint',
        'application_secret',
        'consumer_key'
    ]:
        ckw[i] = kw.setdefault(i, get_ovh_opt(i, domain=domain))
    client = ovh.Client(**ckw)
    return client


def have_rpn():
    _s = __salt__
    providers = _s['mc_provider.settings']()
    have_rpn = providers['have_rpn']
    return have_rpn
# vim:set et sts=4 ts=4 tw=80:
