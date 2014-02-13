PamLdap configuration
=====================

-  install ldap base packages
-  integrate pam with LDAP

Exposed settings:

    :makina-states.localsettings.ldap.enabled: true/false: activate pamldap wiring
    :makina-states.localsettings.ldap.ldap_uri: ldaps://localhost:636/
    :makina-states.localsettings.ldap.ldap_base: dc=company,dc=org
    :makina-states.localsettings.ldap.ldap_passwd: ou=People,dc=company,dc=org?sub
    :makina-states.localsettings.ldap.ldap_shadow: ou=People,dc=company,dc=org?sub
    :makina-states.localsettings.ldap.ldap_group: ou=Group,dc=company,dc=org?sub
    :makina-states.localsettings.ldap.ldap_cacert: /etc/ssl/cacerts/cacert.pem (opt)


