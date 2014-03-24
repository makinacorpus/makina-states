{% if salt['mc_nodetypes.registry']()['is']['devhost'] %}
include:
  - makina-states.cloud.lxc.compute_node.post-setup.devhost
{% endif %}

{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
{% for target, vm in lxcSettings.vm.items() %}
{{target}}-vm-post-setup:
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls:
      - makina-states.services.cloud.lxc.compute_node.post-setup.do
    - concurrent: True
    - watch:
      - mc_proxy: {{target}}-target-post-setup-hook
    - watch_in:
      - mc_proxy: salt-cloud-postdeploy
{% endfor %}
