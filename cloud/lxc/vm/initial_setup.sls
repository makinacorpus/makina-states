{% set reg = salt['mc_cloud_vm.vm_settings']() %}
{% set vmname = reg.mccloud_svmname %}
{% set target = reg.mccloud_stargetname %}
{% set compute_node_settings = reg.cnSettings) %}
{% set data = reg.vtVmData) %}
{% set cloudSettings = reg.cloudSettings) %}
sysadmin-user-initial-password:
  cmd.run:
    - name: >
            for i in ubuntu root sysadmin;do
              echo "${i}:{{data.password}}" | chpasswd && touch /.initialspasses;
            done;
    - unless: test -e /.initialspasses
