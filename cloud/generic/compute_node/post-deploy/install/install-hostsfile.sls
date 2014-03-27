{% set localsettings = salt['mc_localsettings.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set computenode_settings = salt['mc_cloud_compute_node.settings']() %}
include:
  - makina-states.cloud.generic.hooks.compute_node
{% for target, tdata in computenode_settings.targets.items() %}
{% set cptslsname = '{1}/{0}/run-compute_node_hostfile'.format(target.replace('.', ''),
                                                           cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
  - {{cptslsname.replace('/', '.')}}
{%  endfor %}
