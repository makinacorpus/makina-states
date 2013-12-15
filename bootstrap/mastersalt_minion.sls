#
# Boostrap an host an also install a mastersalt wired minion
#
#
# Basic bootstrap is responsible for the setup of saltstack
# Be sure to double check any dependant state there to work if there is
# nothing yet on the VM as it is a "bootstrap stage".
#

include:
  - makina-states.localsettings.base
  - makina-states.bootstrap.base
  - makina-states.services.base.mastersalt

makina-bootstrap-mastersalt-grain:
  grains.present:
    - name: makina.bootstrap.mastersalt
    - value: True
    - require:
      - service: salt-mastersalt-minion

makina-bootstrap-mastersalt-grain:
  grains.present:
    - name: makina.bootstrap.mastersalt_minion
    - value: True
    - require:
      - service: salt-mastersalt-minion

