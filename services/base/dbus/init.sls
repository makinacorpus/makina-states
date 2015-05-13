{{ salt['mc_macros.register']('services', 'base.dbus') }}
include:
  - makina-states.services.proxy.dbus.prerequisites
  - makina-states.services.proxy.dbus.configuration
  - makina-states.services.proxy.dbus.service
