{#- # MasterSalt Minion installation #}
{%- import "makina-states/_macros/salt.jinja" as saltmac with context %}

{{ salt['mc_macros.register']('controllers', 'mastersalt_minion') }}

include:
  - makina-states.controllers.mastersalt

{{ saltmac.install_minion('mastersalt') }}
