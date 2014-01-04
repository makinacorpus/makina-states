#
# Salt Minion installation
#
{% import "makina-states/controllers/salt.sls" as salt with context %}
{% set controllers = salt.controllers %}
{% set saltmac = salt.saltmac %}
{% set name = salt.name + '_minion' %}
{% set localsettings = controllers.localsettings %}
{{ controllers.register(name) }}

include:
  - {{ controllers.funcs.statesPref }}{{salt.name}}

{{ saltmac.install_minion(salt.name) }}
