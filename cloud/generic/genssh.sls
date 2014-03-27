{% set cloudSettings = salt['mc_cloud.settings']() %}
include:
  - makina-states.services.base.ssh.rootkey
  - makina-states.cloud.generic.controller.pre-deploy.install.layout
cloud-root-keygen:
  file.copy:
    - name: {{cloudSettings.root}}/{{cloudSettings.all_sls_dir}}/rootkey-dsa.pub
    - source: /root/.ssh/id_dsa.pub
    - user: root
    - watch:
      - cmd: root-ssh-keys-init
      - file: salt_cloud-dirs
cloud-root-keygen-rsa:
  file.copy:
    - name: {{cloudSettings.root}}/{{cloudSettings.all_sls_dir}}/rootkey-rsa.pub
    - source: /root/.ssh/id_dsa.pub
    - user: root
    - watch:
      - cmd: root-ssh-keys-init
