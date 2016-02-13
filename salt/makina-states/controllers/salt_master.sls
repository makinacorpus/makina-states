{#- # Base server which acts also as a salt master #}
{%- import "makina-states/_macros/salt.jinja" as saltmac with context %}

{{ salt['mc_macros.register']('controllers', 'salt_master') }}

include:
  - makina-states.controllers.salt

{{ saltmac.install_master('salt') }}
