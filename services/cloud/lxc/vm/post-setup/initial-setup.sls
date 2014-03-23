{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
{% set cloudSettings= salt['mc_cloud_controller.settings']() %}

include:
  - makina-states.services.cloud.lxc.hooks

{% for target, vms in lxcSettings.vms.items() %}
{%  for k, data in vms.items() -%}
{%    set data = data.copy() %}
{%    do data.update({'state_name': '{0}-{1}'.format(target, k)})%}
{%    do data.update({'target': target})%}
{%    set sname = data.get('state_name', data['name']) %}
{{sname}}-lxc-client-autostart-at-boot:
  salt.function:
    - tgt: [{{data.target}}]
    - expr_form: list
    - name: cmd.run
    - arg: [{{"'{0}'".format(
"if [ ! -e /etc/lxc/auto ];then mkdir -p /etc/lxc/auto;fi;"
"ln -sf /var/lib/lxc/{sname}/config /etc/lxc/auto/{sname}.conf".format(
            sname=sname))}}]
    - watch:
      - mc_proxy: {{sname}}-lxc-deploy-end-hook
    - watch_in:
      - mc_proxy: {{sname}}-lxc-deploy-pre-initial-highstate
{{sname}}-lxc-sysadmin-user-initial-password:
  salt.function:
    - tgt: [{{data.name}}]
    - expr_form: list
    - name: cmd.run
    - watch:
      - mc_proxy: {{sname}}-lxc-deploy-end-hook
    - watch_in:
      - mc_proxy: {{sname}}-lxc-deploy-pre-initial-highstate
    - arg: ['if [ ! -e /.initialspasses ];then
               for i in ubuntu root sysadmin;do
                 echo "${i}:{{data.password}}" | chpasswd && touch /.initialspasses;
               done;
            fi']
{%   endfor %}
{% endfor %}
