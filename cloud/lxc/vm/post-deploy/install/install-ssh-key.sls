{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
include:
  - makina-states.cloud.generic.hooks.vm
  - makina-states.cloud.generic.genssh
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
{% for target, vms in lxcSettings.vms.items() %}
{% for vmname in vms %}
{% if 'lxc' in compute_node_settings.targets[target].virt_types %}
{% set cptslsname = '{1}/{0}/lxc/{2}/run-install-ssh-key'.format(
        target.replace('.', ''),
        cloudSettings.compute_node_sls_dir,
        vmname.replace('.', '')) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
  - {{cptslsname.replace('/', '.')}}
{% endif %}
{% endfor %}
{% endfor %}
