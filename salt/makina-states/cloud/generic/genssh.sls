{% set cloudSettings = salt['mc_cloud.settings']() %}
include:
  - makina-states.services.base.ssh.rootkey

cloudgenssh-dir:
  file.directory:
    - name: {{cloudSettings.root}}/{{cloudSettings.all_sls_dir}}
    - user: root
    - group: root
    - makedirs: true
cloud-root-keygen:
  file.copy:
    - name: {{cloudSettings.root}}/{{cloudSettings.all_sls_dir}}/rootkey-dsa.pub
    - source: /root/.ssh/id_dsa.pub
    - watch:
      - cmd: root-ssh-keys-init
      - file: cloudgenssh-dir
cloud-root-keygen-rsa:
  file.copy:
    - name: {{cloudSettings.root}}/{{cloudSettings.all_sls_dir}}/rootkey-rsa.pub
    - source: /root/.ssh/id_rsa.pub
    - watch:
      - cmd: root-ssh-keys-init
      - file: cloudgenssh-dir
