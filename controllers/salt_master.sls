{#-
# Base server which acts also as a salt master
#}
{%- import "makina-states/controllers/salt.sls" as salt with context %}
{%- set controllers = salt.controllers %}
{%- set saltmac = salt.saltmac %}
{%- set name = salt.name + '_master' %}
{{ controllers.register(name) }}
include:
  - {{ controllers.statesPref }}{{salt.name}}
{{ saltmac.install_master(salt.name) }}
