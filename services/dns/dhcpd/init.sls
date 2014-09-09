{{ salt['mc_macros.register']('services', 'dns.dhcpd') }}
include:
  - makina-states.services.backup.dbsmartbackup
  - makina-states.services.dns.dhcpd.hooks
  - makina-states.services.dns.dhcpd.prerequisites
  - makina-states.services.dns.dhcpd.configuration
  - makina-states.services.dns.dhcpd.services
