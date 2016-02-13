{{ salt['mc_macros.register']('services', 'virt.docker') }}
include:
  - makina-states.services.virt.docker.hooks
  - makina-states.services.virt.docker.prerequisites
  - makina-states.services.virt.docker.configuration
  - makina-states.services.virt.docker.services
