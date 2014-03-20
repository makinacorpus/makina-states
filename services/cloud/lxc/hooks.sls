{% import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% set cloudSettings= services.cloudSettings %}
{% set lxcSettings = services.lxcSettings %}

include:
  - makina-states.services.virt.lxc-hooks
  - makina-states.services.cloud.cloudcontroller.hooks

{% for target, containers in services.lxcSettings.containers.items() %}
salt-cloud-lxc-{{target}}-ssh-key:
  mc_proxy.hook: []

{%  for k, data in containers.items() -%}
{%    set data = data.copy() %}
{%    do data.update({'state_name': '{0}-{1}'.format(target, k)})%}
{%    do data.update({'target': target})%}
{%    set sname = data.get('state_name', data['name']) %}
{{sname}}-lxc-deploy-start-hook:
  mc_proxy.hook:
    - watch:
      - mc_proxy: lxc-post-inst
      - mc_proxy: salt-cloud-predeploy
      - mc_proxy: salt-cloud-lxc-default-template
      - mc_proxy: salt-cloud-lxc-{{target}}-ssh-key

{{sname}}-lxc-deploy-end-hook:
  mc_proxy.hook:
    - watch:
      - mc_proxy: {{sname}}-lxc-deploy-start-hook

{{sname}}-lxc-ssh-key:
  mc_proxy.hook:
    - watch:
      - mc_proxy: {{sname}}-lxc-deploy-end-hook

{{sname}}-lxc-deploy-pre-initial-highstate:
  mc_proxy.hook:
    - watch:
      - mc_proxy: {{sname}}-lxc-ssh-key
      - mc_proxy: {{sname}}-lxc-deploy-end-hook
    - watch_in:
      - mc_proxy: {{sname}}-lxc-post-setup-hook

{{sname}}-lxc-post-setup-hook:
  mc_proxy.hook:
    - watch_in :
      - {{target}}-target-post-setup-hook
{%  endfor %}

{{target}}-target-post-setup-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: salt-cloud-postdeploy
{% endfor %}

salt-cloud-lxc-images-download:
  mc_proxy.hook: []

salt-cloud-lxc-default-template:
  mc_proxy.hook: []

salt-cloud-lxc-devhost-hooks:
  mc_proxy.hook: []
