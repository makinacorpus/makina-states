{#-
# MasterSalt Minion installation
#}
{% macro do(full=True) %}
{%- import "makina-states/controllers/mastersalt-standalone.sls" as csalt with context %}
{%- set controllers = csalt.controllers %}
{%- set saltmac = csalt.saltmac %}
{%- set name = csalt.name + '_minion' %}
{{ salt['mc_macros.register']('controllers', name) }}
include:
  - makina-states.controllers.{{csalt.name}}
  - makina-states.controllers.hooks
  - makina-states.services.cache.memcached.hooks
  - makina-states.localsettings.git
{{ saltmac.install_minion(csalt.name, full=full) }}
{% endmacro  %}
{{ do(full=False)}}
