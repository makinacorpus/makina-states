{{ salt['mc_macros.register']('services', 'base.dbus') }}
include:
  - makina-states.services.base.dbus.prerequisites
  - makina-states.services.base.dbus.configuration
  - makina-states.services.base.dbus.services
