{{ salt['mc_macros.register']('localsettings', 'nodejs') }}
include:
  - makina-states.localsettings.nodejs.system
{# deactivated by default, we use packaged js for now
  - makina-states.localsettings.nodejs.prefix
#}
