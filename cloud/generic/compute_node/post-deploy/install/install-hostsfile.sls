{% set localsettings = salt['mc_localsettings.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set computenode_settings = salt['mc_cloud_compute_node.settings']() %}
include:
  - makina-states.cloud.generic.hooks.compute_node
{% for target, vm in computenode_settings.vms.items() %}
{% set cptslsname = '{1}/{0}/compute_node_hostfile'.format(target.replace('.', ''),
                                                           cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
cloud-generic-inst-host-postsetup-inst:
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls: {{slsname.replace('/', '.')}}
    - concurrent: True
    - watch:
      - mc_proxy: cloud-generic-compute_node-post-grains-deploy
{%  endfor %}
