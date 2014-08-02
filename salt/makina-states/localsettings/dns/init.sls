{# configure dns resolution #}
{{ salt['mc_macros.register']('localsettings', 'dns') }}
include:
  - makina-states.localsettings.dns.configuration
