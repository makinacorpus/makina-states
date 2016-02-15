{#- # Salt Minion installation #}
{%- import "makina-states/_macros/salt.jinja" as saltmac with context %}

{{ salt['mc_macros.register']('controllers', 'salt_minion') }}

include:
  - makina-states.controllers.salt

{{ saltmac.install_minion('salt') }}
