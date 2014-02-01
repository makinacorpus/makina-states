{#-
# Salt Minion installation
#}
{% macro do(full=True) %}
{%- import "makina-states/controllers/salt-standalone.sls" as csalt with context %}
{%- set controllers = csalt.controllers %}
{%- set saltmac = csalt.saltmac %}
{%- set name = csalt.name + '_minion' %}
{{ salt['mc_macros.register']('controllers', name) }}
include:
  {% if full %}
  - makina-states.controllers.{{csalt.name}}
  {% endif %}
  - makina-states.controllers.salt-hooks
{{ saltmac.install_minion(csalt.name, full=full) }}
{% endmacro %}
{{ do(full=False) }}
