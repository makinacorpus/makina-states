{{ salt['mc_macros.register']('localsettings', 'systemd') }}
#
# special localsettings
# no autoregister please !!!
#
include:
  - makina-states.localsettings.systemd.configuration
  - makina-states.localsettings.systemd.hooks
