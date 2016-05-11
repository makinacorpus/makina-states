{{ salt['mc_macros.register']('localsettings', 'hostname') }}
include:
  - makina-states.localsettings.hostname.hooks
  - makina-states.localsettings.hostname.configuration
