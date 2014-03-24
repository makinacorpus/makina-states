{% set cloudSettings = salt['mc_cloud.settings']() %}
cloud-root-keygen:
  cmd.run:
    - name: ssh-keygen -t dsa
    - user: root
    - unless: test -e /root/.ssh/id_dsa
  file.copy:
    - name: {{cloudSettings.root}}/roopubkey.pub
    - source: /root/.ssh/id_dsa.pub
    - user: root
    - watch:
      - cmd: cloud-root-keygen
