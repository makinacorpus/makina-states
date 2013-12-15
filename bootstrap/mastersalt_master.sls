#
# Boostrap an host an also install a mastersalt wired minion
#
#
# Basic bootstrap is responsible for the setup of saltstack
# Be sure to double check any dependant state there to work if there is
# nothing yet on the VM as it is a "bootstrap stage".
#

include:
  - makina-states.bootstrap.mastersalt_minion
  - makina-states.setups.mastersalt_master

makina-bootstrap-mastersalt-master-grain:
  grains.present:
    - name: makina.bootstrap.mastersalt_master
    - value: True
