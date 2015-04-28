{{ salt['mc_macros.register']('localsettings', 'apparmor') }}
include:
  - makina-states.localsettings.apparmor.prerequisites
  - makina-states.localsettings.apparmor.configuration
  - makina-states.localsettings.apparmor.hooks
