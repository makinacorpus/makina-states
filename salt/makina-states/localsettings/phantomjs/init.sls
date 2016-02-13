{{ salt['mc_macros.register']('localsettings', 'phantomjs') }}
include:
  - makina-states.localsettings.phantomjs.prerequisites
