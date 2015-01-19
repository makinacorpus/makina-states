{% set cloudSettings  = salt['mc_cloud.settings']() %}
insdsakey:
  ssh_auth.present:
    - source: salt://{{cloudSettings.all_sls_dir}}/rootkey-dsa.pub
    - user: root
inskey:
  ssh_auth.present:
    - source: salt://{{cloudSettings.all_sls_dir}}/rootkey-rsa.pub
    - user: root
