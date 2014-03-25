{% set compute_node_settings= salt['mc_cloud_controller.settings']() %}
{% set cloudSettings= salt['mc_cloud.settings']() %}
include:
  - makina-states.cloud.generic.genssh
  - makina-states.cloud.generic.hooks.vm
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
{% for target, vms in lxcSettings.vms.items() %}
{% for vmname, data in vms.items() %}
{% set sname = '{0}-{1}'.format(target, vmname) %}
{% set cptslsname = '{1}/{0}/lxc/{2}/container_ssh_key'.format(
        target.replace('.', ''),
        cloudSettings.compute_node_sls_dir,
        vmname.replace('.', '')) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{{sname}}-lxc.vm-install-ssh-key:
  file.managed:
    - name: {{cptsls}}
    - user: root
    - mode: 750
    - makedirs: true
    - watch:
      - mc_proxy: cloud-generic-vm-pre-install-ssh-key
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-pre-install-ssh-key
    - contents: |
                insdsakey:
                  ssh_auth.present:
                    - source: salt://{{cloudSettings.all_sls_dir}}/rootkey-dsa.pub
                    - user: root
                inskey:
                  ssh_auth.present:
                    - source: salt://{{cloudSettings.all_sls_dir}}/rootkey-rsa.pub
                    - user: root

{% endfor %}
{% endfor %}
