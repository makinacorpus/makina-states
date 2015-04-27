{% include "makina-states/localsettings/dns/macros.sls" with context as dns %}
include:
  - makina-states.localsettings.dns.hooks
{{ dns.switch_dns() }}
