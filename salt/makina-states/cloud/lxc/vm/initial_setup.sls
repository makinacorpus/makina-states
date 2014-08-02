{% set data = salt['mc_cloud_vm.vm_settings']() %} 
sysadmin-user-initial-password:
  cmd.run:
    - name: >
            for i in ubuntu root sysadmin;do
              echo "${i}:{{data.password}}" | chpasswd && touch /.initialspasses;
            done;
    - unless: test -e /.initialspasses
