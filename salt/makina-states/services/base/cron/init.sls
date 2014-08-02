{{ salt['mc_macros.register']('services', 'base.cron') }}
include:
  - makina-states.services.base.cron.prerequisites
  - makina-states.services.base.cron.configuration
  - makina-states.services.base.cron.services
