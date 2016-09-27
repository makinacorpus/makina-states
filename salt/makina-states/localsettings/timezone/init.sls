{#- # tz managment #}
{{ salt['mc_macros.register']('localsettings', 'timezone') }}
include:
  - makina-states.localsettings.timezone.prerequisites
  - makina-states.localsettings.timezone.configuration

