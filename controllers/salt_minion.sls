{#-
# Salt Minion installation
#}
{%- import "makina-states/controllers/salt.sls" as csalt with context %}
{%- set controllers = csalt.controllers %}
{%- set saltmac = csalt.saltmac %}
{%- set name = csalt.name + '_minion' %}
{%- set localsettings = controllers.localsettings %}
{{ salt['mc_macros.register']('controllers', name) }}
include:
  - makina-states.controllers.{{csalt.name}}
{{ saltmac.install_minion(csalt.name) }}
