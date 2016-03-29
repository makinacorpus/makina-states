---
- hosts: "{{makinastates_compute_node}}"
  roles: [makinastates_pillar]

- hosts: "{{makinastates_compute_node}}"
  tasks:
    - include: cloud_compute_node_common.yml
    - include: cloud_compute_node_lxc.yml
