{#-
# Base server which acts also as a salt master
#}
{%- import "makina-states/controllers/salt.sls" as csalt with context %}
{%- set controllers = csalt.controllers %}
{%- set saltmac = csalt.saltmac %}
{%- set name = csalt.name + '_master' %}
{{ salt['mc_macros.register']('controllers', name) }}
include:
  - makina-states.controllers.{{csalt.name}}
{{ saltmac.install_master(csalt.name) }}
