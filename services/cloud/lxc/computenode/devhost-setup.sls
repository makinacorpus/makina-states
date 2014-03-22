{% import "makina-states/_macros/services.jinja" as services with context %}
{% set nodetypes = services.nodetypes %}
{% if nodetypes.registry.is.devhost %}
{% for target, containers in services.lxcSettings.containers.items() %}
{{target}}-containers-post-setup-devhost:
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls:
      - makina-states.services.cloud.lxc.computenode.devhost-sshkeys
      - makina-states.services.cloud.lxc.computenode.devhost-symlinks
    - concurrent: True
    - watch:
      - mc_proxy: {{target}}-target-post-setup-hook
    - watch_in:
      - mc_proxy: salt-cloud-postdeploy
{% endfor %}
{% endif %}
