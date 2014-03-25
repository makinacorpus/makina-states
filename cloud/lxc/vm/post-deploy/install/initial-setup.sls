{% set compute_node_settings = salt['mc_cloud_controller.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
include:
  - makina-states.cloud.generic.hooks.vm

{% for target, vms in lxcSettings.vms.items() %}
{%  for vmname, data in vms.items() -%}
{%    set sname = '{0}-{1}'.format(target, vmname) %}
{% if compute_node_settings.targets[target].virt_types.lxc %}
{{sname}}-lxc-client-autostart-at-boot:
  salt.function:
    - tgt: [{{target}}]
    - expr_form: list
    - name: cmd.run
    - arg: [{{"'{0}'".format(
"if [ ! -e /etc/lxc/auto ];then mkdir -p /etc/lxc/auto;fi;"
"ln -sf /var/lib/lxc/{vmname}/config /etc/lxc/auto/{vmname}.conf".format(vmname=vmname))}}]
    - watch:
      - mc_proxy: cloud-{{vmname}}-generic-vm-pre-initial-setup-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-initial-setup-deploy
{{sname}}-lxc-sysadmin-user-initial-password:
  salt.function:
    - tgt: [{{vmname}}]
    - expr_form: list
    - name: cmd.run
    - watch:
      - mc_proxy: cloud-{{vmname}}-generic-vm-pre-initial-setup-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-initial-setup-deploy
    - arg: ['if [ ! -e /.initialspasses ];then
               for i in ubuntu root sysadmin;do
                 echo "${i}:{{data.password}}" | chpasswd && touch /.initialspasses;
               done;
            fi']
{%   endif %}
{%   endfor %}
{% endfor %}
