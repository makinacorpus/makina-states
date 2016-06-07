{{ salt['mc_macros.register']('localsettings', 'insserv') }}
include:
  - makina-states.localsettings.insserv.configuration
  - makina-states.localsettings.insserv.hooks
