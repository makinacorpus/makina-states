#
# Basic bootstrap is responsible for the setup of saltstack
# Be sure to double check any dependant state there to work if there is
# nothing yet on the VM as it is a "bootstrap stage".
# o
{% set devhost = grains.get('makina.devhost', False) %}

include:
  - makina-states.services.salt_master
  {% if devhost %}- makina-states.services.bootstrap_vm{% endif %}



