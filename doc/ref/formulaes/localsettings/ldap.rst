PamLdap configuration
=====================

- install ldap base packages
- integrate pam with LDAP via nslcd, nss-ldapd pam-ldapd.

Pillar sample:

.. code-block:: yaml

    makina-states.localsettings.ldap:
      ldap_uri: ldap://ldap.foo.net/
      ldap_base: dc=company,dc=org
      ldap_passwd: ou=People,dc=company,dc=org?sub
      ldap_shadow: ou=People,dc=company,dc=org?sub
      ldap_group: ou=Group,dc=company,dc=org?sub
      ldap_cacert: /etc/ssl/cacerts/cacert.pem
      enabled: True
      nslcd:
        ssl: start_tls

Exposed settings:

    :makina-states.localsettings.ldap.enabled: true/false: activate pamldap wiring
    :makina-states.localsettings.ldap.ldap_uri: ldaps://localhost:636/
    :makina-states.localsettings.ldap.ldap_base: dc=company,dc=org
    :makina-states.localsettings.ldap.ldap_passwd: ou=People,dc=company,dc=org?sub
    :makina-states.localsettings.ldap.ldap_shadow: ou=People,dc=company,dc=org?sub
    :makina-states.localsettings.ldap.ldap_group: ou=Group,dc=company,dc=org?sub
    :makina-states.localsettings.ldap.ldap_cacert: /etc/ssl/cacerts/cacert.pem (opt)
    :makina-states.localsettings.ldap.nslcd.ldap_ver: None
    :makina-states.localsettings.ldap.nslcd.scope: sub
    :makina-states.localsettings.ldap.nslcd.user: nslcd
    :makina-states.localsettings.ldap.nslcd.group: nslcd
    :makina-states.localsettings.ldap.nslcd.ssl: start_tls, # ssl, off, start_tls
    :makina-states.localsettings.ldap.nslcd.tls_reqcert: allow
    :makina-states.localsettings.ldap.nslcd.tls_cacert: None
    :makina-states.localsettings.ldap.nslcd.bind_dn: None
    :makina-states.localsettings.ldap.nslcd.bind_pw: None
    :makina-states.localsettings.ldap.nslcd.rootpwmoddn: None
    :makina-states.localsettings.ldap.nslcd.rootpwmodpw: None
    :makina-states.localsettings.ldap.nslcd.bind_timelimit: 30
    :makina-states.localsettings.ldap.nslcd.timelimit: 30
    :makina-states.localsettings.ldap.nslcd.idle_timelimit: 3600
    :makina-states.localsettings.ldap.nslcd.reconnect_sleeptime: 1
    :makina-states.localsettings.ldap.nslcd.reconnect_retrytime: 10



