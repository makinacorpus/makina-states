{% set csettings = salt['mc_cloud.settings']() %}
{% set computenodeSettings = salt['mc_cloud_compute_node.settings']() %}
{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
include:
  - makina-states.cloud.generic.hooks.compute_node
  - makina-states.cloud.generic.genssh
{% for target, vm in lxcSettings.vms.items() %}
{# authorize root from cloudcontroller to connect via ssh on targets #}
{% set cptslsname = '{1}/{0}/install-hosts-ssh-key'.format(target.replace('.', ''),
                                                  csettings.compute_node_sls_dir) %}

{% set cptsls = '{1}/{0}.sls'.format(cptslsname, csettings.root) %}
{{target}}-gen-lxc-host-install-ssh-key:
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls: {{slsname.replace('/', '.')}}
    - concurrent: True
    - watch:
      - mc_proxy: cloud-generic-compute_node-post-grains-deploy
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-host-ssh-key-deploy
{% endfor %}
