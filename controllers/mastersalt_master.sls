#
# Base server which acts also as a mastersalt master
#
{% import "makina-states/_macros/controllers.jinja" as controllers with context %}

{% set name = 'mastersalt_master' %}
{% set saltmac = controllers.saltmac %}
{{ controllers.register(name) }}

include:
  - {{ controllers.statesPref }}mastersalt_minion

{{ saltmac.install_master(saltmac.msaltname) }}
