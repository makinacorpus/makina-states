{{ salt['mc_macros.register']('localsettings', 'npm') }}
include:
  - makina-states.localsettings.npm.system
{#
  - makina-states.localsettings.npm.prefix
#}
