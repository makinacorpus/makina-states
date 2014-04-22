{{ salt['mc_macros.register']('localsettings', 'updatedb') }}
include:
  - makina-states.localsettings.updatedb.configuration
  - makina-states.localsettings.updatedb.prerequisites
