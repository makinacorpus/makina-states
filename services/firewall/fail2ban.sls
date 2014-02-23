{#-
# Install in full mode, see the standalone file !
#}
{% import "makina-states/services/firewall/fail2ban-standalone.sls" as base with context %}
{{ base.do(full=True) }}
