{% set cfg = opts['ms_project'] %}
{% import  "makina-states/projects/{0}/generic/configure.sls".format(cfg['api_version'] as configure with context %}

{% macro do() %}
{{configure.configure_domains(cfg)}}
{% endmacro %}
{{do()}}

