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
  - makina-states.services.vim
  - makina-states.services.git
  - makina-states.services.pkgs
  - makina-states.services.shell
  - makina-states.services.sudo
  - makina-states.services.users

bootstrap:makina-states-server:
  grains.present:
    - value: True
    - require:
      - service: salt-minion
