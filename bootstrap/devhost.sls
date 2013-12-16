# Boostrap an host which is also a contained VM and not a physical machine
#
# Basic bootstrap is responsible for the setup of saltstack
# Be sure to double check any dependant state there to work if there is
# nothing yet on the VM as it is a "bootstrap stage".
#

include:
  - makina-states.bootstrap.server
  - makina-states.setups.devhost

makina-bootstrap-devhost-grain:
  grains.present:
    - name: makina.bootstrap.devhost
    - value: True
