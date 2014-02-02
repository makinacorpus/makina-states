{#- Install in full mode, see the standalone file ! #}
{% import  "makina-states/services/php/fcgid_with_apache-standalone.sls" as base with context %}
{{base.do(full=True)}}
