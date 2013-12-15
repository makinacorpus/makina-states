{% import "makina-states/_macros/salt.jinja" as c with context %}
#
# setup for a salt server
#

include:
  - makina-states.setups.server_salt_minion

makina-nodetype-salt-master-grain:
  grains.present:
    - name: makina.nodetype.salt_master
    - value: True
    - require:
      - service: salt-salt-master
