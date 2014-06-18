{% set data = salt['mc_cloud_vm.vm_settings']() %}
thishost:
  file.managed:
    - name: /this_host
    - contents: "{{data.mccloud_targetname}}"
    - user: root
    - mode: 755

thisip:
  file.managed:
    - name: /this_port
    - contents: "{{data.mccloud_vm_ssh_port}}"
    - user: root
    - mode: 755

