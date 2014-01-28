{#-
# MasterSalt Minion installation
#}
{%- import "makina-states/controllers/mastersalt.sls" as csalt with context %}
{%- set controllers = csalt.controllers %}
{%- set saltmac = csalt.saltmac %}
{%- set name = csalt.name + '_minion' %}
{{ salt['mc_macros.register']('controllers', name) }}
include:
  - makina-states.controllers.{{csalt..name}}
{{ saltmac.install_minion(csalt.name) }}
