{% macro do(full=False) %}
{% if full %}
{% set mode = '' %}
{% else %}
{% set mode = '-standalone' %}
{% endif %}
include:
  - makina-states.services.cloud.salt_cloud{{mode}}
  - makina-states.services.cloud.lxc{{mode}}
  - makina-states.services.cloud.saltify{{mode}}
{% endmacro %}
{{do(full=False)}}
