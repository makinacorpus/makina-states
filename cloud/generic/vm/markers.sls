thishost:
  file.managed:
    - name: /this_host
    - contents: {{pillar.mccloud_targetname}}
    - user: root
    - mode: 755

thisip:
  file.managed:
    - name: /this_port
    - contents: {{pillar.mccloud_vm_ssh_port}}
    - user: root
    - mode: 755

