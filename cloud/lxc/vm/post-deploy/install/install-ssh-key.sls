{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set compute_node_settings = salt['mc_cloud_controller.settings']() %}
{% set saltreg = mc_salt['mc_controllers.settings']() %}
include:
  - makina-states.cloud.generic.hooks.vm
  - makina-states.cloud.generic.genssh
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
{% for target, vms in lxcSettings.vms.items() %}
{% for vmname, data in vms.items() %}
{% if compute_node_settings.targets[target].virt_types.lxc %}
{% set sname = data.get('state_name', '{0}-{1}'.format(target, k) %}
{% set cptslsname = '{1}/{0}/lxc/{2}/container_ssh_key'.format(
        target.replace('.', ''),
        cloudSettings.vms_sls_dir,
        vmname,
        vmname.replace('.', '')) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{{sname}}-lxc.vm-install-ssh-key:
  salt.state:
    - tgt: [{{vmname}}]
    - expr_form: list
    - sls: {{cptslsname.replace('/', '.')}}
    - concurrent: True
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-pre-install-ssh-key
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-install-ssh-key
{% endif %}
{% endfor %}
{% endfor %}
