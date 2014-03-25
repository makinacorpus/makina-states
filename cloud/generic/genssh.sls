{% set cloudSettings = salt['mc_cloud.settings']() %}
include:
  - makina-states.services.base.ssh.rootkey
cloud-root-keygen:
  file.copy:
    - name: {{cloudSettings.root}}/roopubkey.pub
    - source: /root/.ssh/id_dsa.pub
    - user: root
    - watch:
      - cmd: root-ssh-keys-init
cloud-root-keygen-rsa:
  file.copy:
    - name: {{cloudSettings.root}}/roopubkey-rsa.pub
    - source: /root/.ssh/id_dsa.pub
    - user: root
    - watch:
      - cmd: root-ssh-keys-init
