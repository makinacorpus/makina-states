#!/usr/bin/ldap ldap
# -*- coding: utf-8 -*-
'''

.. _module_mc_ldap:

mc_ldap / ldap registry
============================================


'''
# Import ldap libs
import sys
import logging
import mc_states.api
from contextlib import contextmanager
import salt.utils.odict
try:
    import ldap
    HAS_LDAP = True
except ImportError:
    HAS_LDAP = False

_marker = object()
_HANDLERS = {}

__name = 'ldap'

log = logging.getLogger(__name__)

if sys.version > 3:
    unicode  = str


def settings(saltmods=None):
    '''
    ldap registry

        use nslcd / pamldapd or pamldap (on lenny)::

                'enabled': False,
                'nslcd': {
                    'ldap_ver': None,  # '3',
                    'scope': 'sub',
                    'user': 'nslcd',
                    'group': 'nslcd',
                    'ssl': 'off',  # ssl, off, start_tls
                    'tls_reqcert': 'never',
                    'tls_cacert': None,
                    'bind_dn': None,
                    'bind_pw': None,
                    'rootpwmoddn': None,
                    'rootpwmodpw': None,
                    # for setting the connection time out.
                    # The default bind_timelimit is 10 seconds.
                    # Specifies  the  time  limit (in seconds) to use when
                    # connecting to the directory server.  This is distinct
                    # from the time limit specified in timelimit and affects
                    # the set-up of the connection only.
                    # Note that not all LDAP client libraries have support
                    'bind_timelimit': '30',
                    # Specifies the time limit (in seconds) to wait for a
                    # response from the LDAP server.  A value of zero (0),
                    # which is the default, is to wait indefinitely for
                    # searches to be completed.
                    'timelimit': '30',
                    # Specifies the period if inactivity (in seconds) after which
                    # the connection to the LDAP server will be closed.
                    # The default is not to time out connections.
                    'idle_timelimit': '3600',
                    #Specifies the number of seconds to sleep when connecting
                    # to all LDAP servers fails.  By default 1 second is
                    # waited between the first failure and the first retry.
                    'reconnect_sleeptime': '1',
                    # Specifies the time after which the LDAP server is considered
                    # be permanently unavailable.  Once this time is reached retrie
                    # will be done only once per this time period.
                    # The default value is 10 seconds.
                    # Note that the reconnect logic as described above is the
                    # mechanism that is used between nslcd and the LDAP server.
                    # The mechanism between the NSS and PAM client libraries on
                    # one end and nslcd on the other is simpler with a fixed
                    # compiled-in time out of  a  10
                    # seconds for writing to nslcd and a time out of 60 seconds
                    # for reading answers.  nslcd itself has a read time out
                    # of 0.5 seconds and a write time out of 60 seconds.
                   'reconnect_retrytime': '10',
                'ldap_uri': 'ldaps://localhost:636/',
                'ldap_base': 'dc=company,dc=org',
                'ldap_passwd': 'ou=People,dc=company,dc=org?sub',
                'ldap_shadow': 'ou=People,dc=company,dc=org?sub',
                'ldap_group': 'ou=Group,dc=company,dc=org?sub',
                'ldap_cacert': ''
                'tlscheckpeer': 'yes',
                'pamldap_ssl': 'no',
                'ldap_cacert': ''
                'tlscheckpeer': 'yes',
                'pamldap_ssl': 'no',

    '''
    if saltmods is not None:
        globals()['__salt__'] = saltmods
    @mc_states.api.lazy_subregistry_get(__salt__, __name)
    def _settings():
        saltmods = __salt__
        grains = __grains__
        pillar = __pillar__
        # see makina-states.services.base.ldap
        lsettings = saltmods['mc_utils.defaults'](
            'makina-states.localsettings.ldap', {
                'enabled': False,
                'nslcd': {
                    'ldap_ver': None,  # '3',
                    'scope': 'sub',
                    'user': 'nslcd',
                    'group': 'nslcd',
                    'ssl': 'off',  # ssl, off, start_tls
                    'tls_reqcert': 'never',
                    'tls_cacert': None,
                    'bind_dn': None,
                    'bind_pw': None,
                    'rootpwmoddn': None,
                    'rootpwmodpw': None,
                    'bind_timelimit': '30',
                    'timelimit': '30',
                    'idle_timelimit': '3600',
                    'reconnect_sleeptime': '1',
                    'reconnect_retrytime': '10',

                },
                'ldap_uri': 'ldaps://localhost:636/',
                'ldap_base': 'dc=company,dc=org',
                'ldap_passwd': 'ou=People,dc=company,dc=org?sub',
                'ldap_shadow': 'ou=People,dc=company,dc=org?sub',
                'ldap_group': 'ou=Group,dc=company,dc=org?sub',
                'tlscheckpeer': 'yes',
                'pamldap_ssl': 'no',
                'ldap_cacert': ''
            })
        if lsettings['ldap_cacert'] and not lsettings['nslcd']['tls_cacert']:
            lsettings['nslcd']['tls_cacert'] = lsettings['ldap_cacert']
        return lsettings
    return _settings()


def ldapEn(saltmods):
    return settings(saltmods).get('enabled', False)


class _ConnectionHandler(object):

    def __init__(self,
                 uri,
                 base=None,
                 user=None,
                 password=None,
                 tls=None,
                 retrieve_attributes=None,
                 scope=None):
        if tls is None:
            tls = True
        if not scope:
            scope = 'subtree'
        self.scope = getattr(ldap, 'SCOPE_{0}'.format(scope.upper()),
                             'SCOPE_SUBTREE')
        self.tls = tls
        if retrieve_attributes is None:
            retrieve_attributes = []
        self.retrieve_attributes = retrieve_attributes
        self.uri = uri
        self.user = user
        self.password = password
        self.conns = salt.utils.odict.OrderedDict()
        self.base = base

    def query(self,
              search,
              retrieve_attributes=None,
              conn=None,
              base=None,
              scope=None):
        results = None
        if conn is None:
            conn = self.connect()
        if base is None:
            base = self.base
        if scope is None:
            scope = self.scope
        if isinstance(scope,  (str, unicode)):
            scope = {'ONE': 'ONELEVEL'}.get(scope.upper(), scope.upper())
            scope = getattr(ldap, 'SCOPE_{0}'.format(scope.upper()))
        if retrieve_attributes is None:
            retrieve_attributes = self.retrieve_attributes
        if base is None:
            raise ValueError('Please select a base')
        if not search:
            search = 'objectClass=top'
        results = conn.search_st(base,
                                 scope,
                                 search,
                                 retrieve_attributes,
                                 timeout=60)
        return results

    def unbind(self, disconnect=None):
        if isinstance(disconnect, tuple):
            disconnect = [disconnect]
        elif disconnect is None:
            disconnect = [a for a in self.conns]
        for connid in disconnect:
            try:
                self.conns[connid].unbind()
            except:
                pass
            self.conns.pop(connid, None)

    def connect(self):
        conn = self.conns.get((self.uri, self.user), _marker)
        if conn is _marker:
            conn = ldap.initialize(self.uri)
            if self.tls:
                conn.start_tls_s()
            if self.user:
                conn.simple_bind_s(self.user, self.password)
            else:
                conn.simple_bind()
            self.conns[(self.uri, self.user)] = conn
        return conn


@contextmanager
def get_handler(uri, **ckw):
    '''
    Helper to handle a pool of ldap connexion and gracefully disconnects

    This use the previous _ConnectionHandler on the behalf of a connexion
    manager to handle gracefully connection and deconnection.

      uri
        ldap url
      base
        base to search
      user
        user dn
      password
        password
      tls
        activate tls encryption
      retrieve_attributes
        default query retrieved attributes
      scope
        default query scope

    .. code-block:: python

        with get_handler("ldap://ldap.foo.net",
                           base="dc=foo,dc=org",
                           user="uid=xxx,ou=People,dc=x",
                                password="xxx") as h:
            h.query('objectClass=person')
            h.query('objectClass=groupOfNames')

    '''
    if not HAS_LDAP:
        raise IndexError('pythonldap is required')
    kw = {}
    for i in [a for a in ckw if not a.startswith('__')]:
        kw[i] = ckw[i]
    handler = _HANDLERS.get(uri, _marker)
    if handler is _marker:
        _HANDLERS[uri] = _ConnectionHandler(uri, **kw)
    try:
        yield _HANDLERS[uri]
    finally:
        _HANDLERS[uri].unbind()
        _HANDLERS.pop(uri, None)

# vim:set et sts=4 ts=4 tw=80:
