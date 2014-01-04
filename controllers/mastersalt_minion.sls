#
# MasterSalt Minion installation
#
{% import "makina-states/controllers/mastersalt.sls" as salt with context %}
{% set controllers = salt.controllers %}
{% set saltmac = salt.saltmac %}
{% set name = salt.name + '_minion' %}
{{ controllers.register(name) }}

include:
  - {{ controllers.statesPref }}{{salt.name}}

{{ saltmac.install_minion(salt.name) }}
