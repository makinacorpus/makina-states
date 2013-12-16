#
# Basic bootstrap is responsible for the setup of saltstack
# Be sure to double check any dependant state there to work if there is
# nothing yet on the VM as it is a "bootstrap stage".
#

include:
  - makina-states.bootstrap.base
  - makina-states.setups.salt_minion

makina-bootstrap-salt-minion-grain:
  grains.present:
    - name: makina.bootstrap.salt_minion
    - value: True
