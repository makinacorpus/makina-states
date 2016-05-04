{{ salt['mc_macros.register']('localsettings', 'hosts') }}
include:
  - makina-states.localsettings.hosts.hooks
  - makina-states.localsettings.hosts.configuration
