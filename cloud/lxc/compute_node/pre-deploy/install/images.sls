include:
  - makina-states.cloud.generic.hooks.compute_node
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set csettings = salt['mc_cloud_compute_node.settings']() %}
{% for target, data in csettings['targets'].items() %}
{% if data.virt_types.lxc %}
{% set cptslsname = '{1}/{0}/lxc/images-templates'.format(target.replace('.', ''),
                                                  cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{{target}}-install-lxc-images-templates:
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls: {{cptslsname.replace('/', '.')}}
    - concurrent: True
    - watch:
      - mc_proxy: cloud-{{name}}-generic-compute_node-pre-images-deploy
    - watch_in:
      - mc_proxy: cloud-{{name}}-generic-compute_node-post-images-deploy
{% endif %}
{% endfor %}
maybe-only-one-inst-lxc-images:
  mc_proxy.hook : []
