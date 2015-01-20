{% set data = salt['mc_cloud_vm.vm_settings']() %}
thishost:
  file.managed:
    - name: /this_host
    - contents: "{{data.target}}"
    - user: root
    - mode: 755

thisip:
  file.managed:
    - name: /this_port
    - contents: "{{data.ssh_reverse_proxy_port}}"
    - user: root
    - mode: 755

