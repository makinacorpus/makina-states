{% import "makina-states/_macros/services.jinja" as services with context %}
{% for target, containers in services.lxcSettings.containers.items() %}
{{target}}-containers-post-setup:
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls:
      - makina-states.services.cloud.lxc.computenode.post-setup
    - concurrent: True
    - watch:
      - mc_proxy: {{target}}-target-post-setup-hook
    - watch_in:
      - mc_proxy: salt-cloud-postdeploy
{% endfor %}
