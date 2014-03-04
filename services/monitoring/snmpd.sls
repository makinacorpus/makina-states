{#- Install in full mode, see the standalone file ! #}
{% import "makina-states/services/monitoring/snmpd-standalone.sls" as base with context %}
{{ base.do(full=True) }}
