{#- Install in full mode, see the standalone file ! #}
{% import  "makina-states/services/dns/bind-standalone.sls" as base with context %}
{{base.do(full=True)}}
