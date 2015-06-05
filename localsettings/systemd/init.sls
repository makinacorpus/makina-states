{{ salt['mc_macros.register']('localsettings', 'ssystemd') }}
#
# special localsettings
# no autoregister please !!!
#
include:
  - makina-states.localsettings.systemd.configuration
  - makina-states.localsettings.systemd.hooks
