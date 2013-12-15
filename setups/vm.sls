#
# extra setup on VM
#

makina-nodetype-vm-grain:
  grains.present:
    - name: makina.nodetype.vm
    - value: True
