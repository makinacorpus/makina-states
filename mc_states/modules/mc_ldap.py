#!/usr/bin/ldap ldap
# -*- coding: utf-8 -*-
'''

.. _module_mc_ldap:

mc_ldap / ldap registry
============================================

If you alter this module and want to test it, do not forget
to deploy it on minion using::

  salt '*' saltutil.sync_modules

Documentation of this module is available with::

  salt '*' sys.doc mc_ldap

'''
# Import ldap libs
import logging
import mc_states.utils

__name = 'ldap'

log = logging.getLogger(__name__)


def settings(saltmods=None):
    '''
    ldap registry

        use nslcd / pamldapd or pamldap (on lenny)

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
    @mc_states.utils.lazy_subregistry_get(__salt__, __name)
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


def dump():
    return mc_states.utils.dump(__salt__,__name)

#
# -*- coding: utf-8 -*-
__docformat__ = 'restructuredtext en'

# vim:set et sts=4 ts=4 tw=80:
