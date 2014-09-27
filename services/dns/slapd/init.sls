{{ salt['mc_macros.register']('services', 'dns.slapd') }}
include:
  - makina-states.services.backup.dbsmartbackup
  - makina-states.services.dns.slapd.hooks
  - makina-states.services.dns.slapd.prerequisites
  - makina-states.services.dns.slapd.configuration
  - makina-states.services.dns.slapd.services
