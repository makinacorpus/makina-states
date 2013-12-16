{% import "makina-states/_macros/salt.jinja" as c with context %}
# Basic bootstrap is responsible for the setup of saltstack
# Be sure to double check any dependant state there to work if there is
# nothing yet on the VM as it is a "bootstrap stage".


include:
  - makina-states.bootstrap.salt_minion
  - makina-states.setups.salt_master

makina-bootstrap-salt-master-grain:
  grains.present:
    - name: makina.bootstrap.salt_master
    - value: True
makina-bootstrap-salt-master-grain:
  grains.present:
    - name: makina.bootstrap.salt_master
    - value: True
