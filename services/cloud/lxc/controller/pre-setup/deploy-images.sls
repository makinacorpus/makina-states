include:
  - makina-states.services.cloud.lxc.hooks
{% import "makina-states/_macros/services.jinja" as services with context %}
{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
{% set targets = [grains['id']] %}
{% for target in lxcSettings.vms %}
{%  if target not in targets %}
{%    do targets.append(target) %}
{%  endif %}
{% endfor %}
{% for target in targets %}
{{target}}-lxc-images-install:
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls: makina-states.services.cloud.lxc.compute_node.host-images-managment
    - concurrent: True
    - watch_in:
      - mc_proxy: salt-cloud-lxc-default-template
{%endfor%}
