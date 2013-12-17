#
# Base server which acts also as a salt master
#

{% import "makina-states/_macros/controllers.jinja" as controllers with context %}

{% set name = 'salt_master' %}
{% set saltmac = controllers.saltmac %}
{{ controllers.register(name) }}

include:
  - {{ controllers.statesPref }}salt_minion

{{ saltmac.install_master(saltmac.saltname) }}
