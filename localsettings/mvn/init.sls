{{ salt['mc_macros.register']('localsettings', 'mvn') }}
include:
  - makina-states.localsettings.mvn.hooks
  - makina-states.localsettings.mvn.prerequisites
