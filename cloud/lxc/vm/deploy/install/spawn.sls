{% set localsettings = salt['mc_localsettings.settings']() %}
include:
  - makina-states.cloud.generic.hooks.vm
{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% macro lxc_container(data) %}
{% set sname = data.get('state_name', data['name']) %}
{% set vmname = data['name'] %}
{% set dnsservers = data.get("dnsservers", ["8.8.8.8", "4.4.4.4"]) -%}
{{sname}}-lxc-deploy:
  cloud.profile:
    - name: {{vmname}}
    - profile: {{data.get('profile', 'ms-{0}-dir-sratch'.format(data['target']))}}
    - unless: test -e {{cloudSettings.prefix}}/pki/master/minions/{{vmname}}
    - watch:
      - mc_proxy: cloud-{{vmname}}-generic-vm-pre-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-deploy
    - minion: {master: "{{data.master}}",
               master_port: {{data.master_port}}}
    - dnsservers: {{dnsservers|yaml}}
{%    for var in ["from_container",
                   "snapshot",
                   "image",
                   "gateway",
                   "bridge",
                   "mac",
                   "ssh_gateway",
                   "ssh_gateway_user",
                   "ssh_gateway_port",
                   "ssh_gateway_key",
                   "ip",
                   "netmask",
                   "size",
                   "backing",
                   "vgname",
                   "lvname",
                   "script_args",
                   "dnsserver",
                   "ssh_username",
                   "password",
                   "lxc_conf",
                   "lxc_conf_unset"] %}
{%      if data.get(var) %}
    - {{var}}: {{data[var]}}
{%      endif%}
{%    endfor%}
{% endmacro %}
{% for target, vms in lxcSettings.vms.items() %}
{%  for vmname, data in vms.items() -%}
{%    set data = data.copy() %}
{%    do data.update({'state_name': '{0}-{1}'.format(target, vmname)})%}
{%    do data.update({'target': target})%}
{{ lxc_container(data) }}
{%  endfor %}
{% endfor %}
