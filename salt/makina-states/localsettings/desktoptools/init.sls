{{ salt['mc_macros.register']('localsettings', 'desktoptools') }}
include:
  - makina-states.localsettings.desktoptools.prerequisites
  - makina-states.localsettings.desktoptools.configuration
  - makina-states.localsettings.desktoptools.hooks
