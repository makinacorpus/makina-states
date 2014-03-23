{% set localsettings = salt['mc_localsettings.settings']() %}
{% set cloudSettings= salt['mc_cloud_settings.settings']() %}
{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}

include:
  - makina-states.services.virt.lxc-hooks
  - makina-states.services.cloud.cloudcontroller.hooks

{% for target, vm in lxcSettings.vm.items() %}
salt-cloud-lxc-{{target}}-pre-setup:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: salt-cloud-lxc-{{target}}-ssh-key
salt-cloud-lxc-{{target}}-ssh-key:
  mc_proxy.hook: []

{%  for k, data in vm.items() -%}
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
