{#- Install in full mode, see the standalone file ! #}
{% import  "makina-states/services/php/fcgid_common-standalone.sls" as base with context %}
{% set includes = base.includes %}
{% set do = base.do %}
{{base.do(full=True)}}
