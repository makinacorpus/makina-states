{% set localsettings = salt['mc_localsettings.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set computenode_settings = salt['mc_cloud_compute_node.settings']() %}
include:
  - makina-states.cloud.generic.hooks.compute_node
{% for target, tdata in computenode_settings.targets.items() %}
{% set cptslsname = '{1}/{0}/compute_node_hostfile'.format(target.replace('.', ''),
                                                           cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{{target}}-cloud-generic-inst-host-postsetup-inst:
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls: {{cptslsname.replace('/', '.')}}
    - concurrent: True
    - watch:
      - mc_proxy: cloud-{{target}}-generic-compute_node-pre-hostsfiles-deploy
    - watch_in:
      - mc_proxy: cloud-{{target}}-generic-compute_node-post-hostsfiles-deploy
{%  endfor %}
