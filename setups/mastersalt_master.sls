{% import "makina-states/_macros/salt.jinja" as c with context %}
include:
  - makina-states.setups.mastersalt_minion
  - makina-states.services.base.mastersalt_master

makina-nodetype-mastersalt-master-grain:
  grains.present:
    - name: makina.nodetype.mastersalt_master
    - value: True
    - require:
      - service: salt-mastersalt-master
