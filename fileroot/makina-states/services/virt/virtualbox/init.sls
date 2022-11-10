{{ salt['mc_macros.register']('services', 'virt.virtualbox') }}
include:
  - makina-states.services.virt.virtualbox.hooks
  - makina-states.services.virt.virtualbox.prerequisites
  - makina-states.services.virt.virtualbox.configuration
  - makina-states.services.virt.virtualbox.services
