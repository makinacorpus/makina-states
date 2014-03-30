{{ salt['mc_macros.register']('services', 'virt.lxc') }}
include:
  - makina-states.services.virt.lxc.prerequisites
  - makina-states.services.virt.lxc.configuration
  - makina-states.services.virt.lxc.hooks

