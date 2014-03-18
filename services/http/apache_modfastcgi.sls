{#- Install in full mode, see the standalone file ! #}
{% import  "makina-states/services/http/apache_modfastcgi-standalone.sls" as base with context %}
{% set includes = base.includes %}
{% set do = base.do %}
{{base.do(full=True)}}
