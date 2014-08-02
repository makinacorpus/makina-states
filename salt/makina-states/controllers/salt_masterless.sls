{#- # Base server which acts also as a mastersalt master #}
{%- import "makina-states/_macros/salt.jinja" as saltmac with context %}

{{ salt['mc_macros.register']('controllers', 'salt_masterless') }}

include:
  - makina-states.controllers.salt
  - makina-states.services.cache.memcached
