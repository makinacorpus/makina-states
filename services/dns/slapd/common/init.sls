{{ salt['mc_macros.register']('services', 'dns.slapd.common') }}
include:
  - makina-states.services.dns.ldap.hooks
  - makina-states.services.dns.ldap.common.prerequisites
  - makina-states.services.dns.ldap.common.configuration
  - makina-states.services.dns.ldap.common.services
