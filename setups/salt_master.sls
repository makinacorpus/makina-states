{% import "makina-states/_macros/salt.jinja" as c with context %}
#
# setup for a salt server
#

include:
  - makina-states.services.base.salt_master
  - makina-states.setups.salt_minion

makina-nodetype-salt-master-grain:
  grains.present:
    - name: makina.nodetype.salt_master
    - value: True
