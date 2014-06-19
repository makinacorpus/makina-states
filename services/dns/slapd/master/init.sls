{{ salt['mc_macros.register']('services', 'dns.slapd.master') }}
include:
  - makina-states.services.dns.ldap.hooks
  - makina-states.services.dns.ldap.common
  - makina-states.services.dns.ldap.master.configuration
