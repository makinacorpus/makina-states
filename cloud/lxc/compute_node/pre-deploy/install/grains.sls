include:
  - makina-states.cloud.generic.hooks.compute_node
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% for target, data in compute_node_settings['targets'].items() %}
{% if 'lxc' in data.virt_types %}
{% set cptslsname = '{1}/{0}/lxc/run-computenode_lxc_grains'.format(target.replace('.', ''),
                                                  cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
  - {{cptslsname.replace('/', '.')}}
{% endif %}
{% endfor %}
maybe-only-one-inst-lxc-grains:
  mc_proxy.hook : []
