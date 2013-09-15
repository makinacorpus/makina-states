#
# Alias for bootstrap server to really mean 'not wired to mastersalt'
#
#
# Basic bootstrap is responsible for the setup of saltstack
# Be sure to double check any dependant state there to work if there is
# nothing yet on the VM as it is a "bootstrap stage".
#

include:
  - makina-states.services.bootstrap_server

bootstrap:makina-states-standalone:
  grains.present:
    - value: True
    - require:
      - service: salt-minion

