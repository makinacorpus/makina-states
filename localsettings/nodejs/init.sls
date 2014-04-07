{{ salt['mc_macros.register']('localsettings', 'nodejs') }}
include:
  - makina-states.localsettings.nodejs.system
  - makina-states.localsettings.nodejs.prefix
