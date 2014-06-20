{% set data = salt['mc_cloud_vm.vm_settings']() %}
{% set cloudSettings = data.cloudSettings %}
include:
    - makina-states.services.base.ssh.rootkey
insdsakey:
  ssh_auth.present:
    - source: salt://{{cloudSettings.all_sls_dir}}/rootkey-dsa.pub
    - user: root
inskey:
  ssh_auth.present:
    - source: salt://{{cloudSettings.all_sls_dir}}/rootkey-rsa.pub
    - user: root
