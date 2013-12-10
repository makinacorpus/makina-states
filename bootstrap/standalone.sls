#
# do no install stuff from makina-states, just drop the
# makina-states master/minion
#

include:
  - makina-states.bootstrap.base
  - makina-states.services.base.salt
  - makina-states.services.base.salt_master

makina-bootstrap-standalone-grain:
  grains.present:
    - name: makina.bootstrap.standalone
    - value: True
    - require:
      - service: salt-salt-minion

