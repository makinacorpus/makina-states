{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
{% if salt['mc_nodetypes.registry']()['is']['devhost'] %}
{% for target, vm in lxcSettings.vm.items() %}
{{target}}-vm-post-setup-devhost:
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls:
      - makina-states.services.cloud.lxc.compute_node.post-setup.devhost.sshkeys
      - makina-states.services.cloud.lxc.compute_node.post-setup.devhost.symlinks
    - concurrent: True
    - watch:
      - mc_proxy: {{target}}-target-post-setup-hook
    - watch_in:
      - mc_proxy: salt-cloud-postdeploy
{% endfor %}
{% else %}
lxc-host-setup-on-devhost:
  mc_proxy.hook: []
{% endif %}
