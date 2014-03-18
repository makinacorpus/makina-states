{#- Install in full mode, see the standalone file ! #}
{% import  "makina-states/services/php/phpfpm-standalone.sls" as base with context %}
{% set do = base.do %}
{{ base.do(full=True) }}
