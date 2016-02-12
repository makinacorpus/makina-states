{{ salt['mc_macros.register']('services', 'log.ulogd') }}
include:
  - makina-states.services.log.ulogd.hooks
  - makina-states.services.log.ulogd.prerequisites
  - makina-states.services.log.ulogd.configuration
  - makina-states.services.log.ulogd.services
