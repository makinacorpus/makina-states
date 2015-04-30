{{ salt['mc_macros.register']('localsettings', 'autoupgrade') }}
include:
  - makina-states.localsettings.autoupgrade.prerequisites
  - makina-states.localsettings.autoupgrade.configuration
  - makina-states.localsettings.autoupgrade.hooks
