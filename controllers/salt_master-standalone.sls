{#-
# Base server which acts also as a salt master
#}
{% macro do(full=True) %}
{%- import "makina-states/controllers/salt-standalone.sls" as csalt with context %}
{%- set controllers = csalt.controllers %}
{%- set saltmac = csalt.saltmac %}
{%- set name = csalt.name + '_master' %}
{{ salt['mc_macros.register']('controllers', name) }}
include:
  - makina-states.controllers.{{csalt.name}}
  - makina-states.controllers.hooks
  - makina-states.services.cache.memcached.hooks
{{ saltmac.install_master(csalt.name, full=full) }}
{% endmacro  %}
{{ do(full=False)}}
