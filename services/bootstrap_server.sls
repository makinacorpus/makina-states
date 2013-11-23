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
# nothing yet on the VM as it is a "bootstrap stage".
#

include:
  - makina-states.services.bootstrap
  - makina-states.localsettings.vim
  - makina-states.localsettings.git
  - makina-states.localsettings.pkgs
  - makina-states.localsettings.shell
  - makina-states.localsettings.sudo
  - makina-states.localsettings.users

makina-bootstrap-server-grain:
  grains.present:
    - name: makina.bootstrap.server
    - value: True
    - require:
      - service: salt-minion
