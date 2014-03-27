include:
  - makina-states.cloud.generic.hooks.compute_node
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% for target, data in compute_node_settings['targets'].items() %}
{% set cptslsname = '{1}/{0}/run-compute_node_firewall'.format(target.replace('.', ''),
                                                  cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
  - {{cptslsname.replace('/', '.')}}
{% endfor %}
