{{ salt['mc_macros.register']('services', 'dns.bind') }}
include:
  - makina-states.services.dns.bind.hooks
  - makina-states.services.dns.bind.prerequisites
  - makina-states.services.dns.bind.configuration
  - makina-states.services.dns.bind.services
