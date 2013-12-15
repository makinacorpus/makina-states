#
# extra setup on a basic server
#

makina-nodetype-server-grain:
  grains.present:
    - name: makina.nodetype.server
    - value: True

