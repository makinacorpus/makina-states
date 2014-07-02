{{ salt['mc_macros.register']('localsettings', 'casperjs') }}
include:
  - makina-states.localsettings.phantomjs
  - makina-states.localsettings.casperjs.prerequisites
