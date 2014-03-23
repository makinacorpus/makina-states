include:
  - makina-states.cloud.lxc.hooks
{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
{% for target, vm in lxcSettings.vm.items() %}
{{target}}-vm-post-setup:
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls:
      - makina-states.services.cloud.lxc.compute_node.pre-setup.do
    - concurrent: True
    - watch_in:
      - mc_proxy: salt-cloud-lxc-{{target}}-pre-setup
    - watch:
      - mc_proxy: salt-cloud-predeploy
{% endfor %}
