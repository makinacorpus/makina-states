#
# Boostrap an host:
#   - install base packages
#   - configure editor
#   - configure shell
#   - configure sudoers
#   - install base saltstack minions, master and file layouts
#   - configure base users
#   - configure ldap if enabled
#
# Basic bootstrap is responsible for the setup of saltstack
# Be sure to double check any dependant state there to work if there is
# nothing yet on the BOX as it is a "bootstrap stage".
#

include:
  - makina-states.bootstrap.base
  - makina-states.setups.server

makina-bootstrap-server-grain:
  grains.present:
    - name: makina.bootstrap.server
    - value: True
