{#- # Base server which acts also as a mastersalt master #}
{%- import "makina-states/_macros/salt.jinja" as saltmac with context %}

{{ salt['mc_macros.register']('controllers', 'mastersalt_masterless') }}

include:
  - makina-states.controllers.mastersalt
  - makina-states.services.cache.memcached
