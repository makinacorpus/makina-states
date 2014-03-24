include:
  - makina-states.cloud.generic.hooks.vm
{% set csettings = salt['mc_cloud.settings']() %}
{% set settings = salt['mc_cloud_compute_node.settings']() %}
{% for target, data in settings['targets'].iteritems() %}
{% if data.has.lxc %}
{% set cptslsname = '{1}/{0}/lxc-images-templates'.format(target.replace('.', ''),
                                                  csettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, csettings.root) %}
{{target}}-install-lxc-images-templates:
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls: {{cptslsname.replace('/', '.')}}
    - concurrent: True
    - watch:
      - mc_proxy: cloud-generic-vm-pre-images-deploy
    - watch_in:
      - mc_proxy: cloud-generic-vm-post-images-deploy
{% endif %}
{% endfor %}
maybe-only-one-inst-lxc-images:
  mc_proxy.hook : []
