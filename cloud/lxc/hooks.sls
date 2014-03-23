{% set localsettings = salt['mc_localsettings.settings']() %}
{% set cloudSettings= salt['mc_cloud_settings.settings']() %}
{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}

include:
  - makina-states.services.virt.lxc-hooks
  - makina-states.cloud.cloudcontroller.hooks
  - makina-states.cloud.saltify.hooks

{% for target, vm in lxcSettings.vm.items() %}
cloud-lxc-{{target}}-pre-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-lxc-{{target}}-ssh-key

cloud-lxc-{{target}}-ssh-key:
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
      - mc_proxy: cloud-pre-deploy
      - mc_proxy: cloud-lxc-default-template
      - mc_proxy: cloud-lxc-{{target}}-ssh-key

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
      - mc_proxy: cloud-lxc-{{target}}-post-deploy
{%  endfor %}

cloud-lxc-{{target}}-post-deploy:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-post-deploy
{% endfor %}

cloud-lxc-images-download:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre-pre-setup
    - watch_in:
      - mc_proxy: cloud-generic-pre-post-setup

cloud-lxc-default-template:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre-pre-setup
    - watch_in:
      - mc_proxy: cloud-generic-pre-post-setup

cloud-lxc-devhost-hooks:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre-post-setup
    - watch_in:
      - mc_proxy: cloud-generic-post-post-setup

