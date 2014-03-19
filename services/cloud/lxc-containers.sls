{% import "makina-states/_macros/services.jinja" as services with context %}
{% set cloudSettings= services.cloudSettings %}
{% set lxcSettings = services.lxcSettings %}
{% set pvdir = cloudSettings.pvdir %}
{% set pfdir = cloudSettings.pfdir %}
{% set localsettings = services.localsettings %}
include:
  {# lxc may not be installed directly on the cloud controller ! #}
  - makina-states.services.virt.lxc-hooks
  - makina-states.services.cloud.salt_cloud-hooks
  - makina-states.services.cloud.lxc-hooks
{% macro lxc_container(data) %}
{% set sname = data.get('state_name', data['name']) %}
{% set name = data['name'] %}
{% set dnsservers = data.get("dnsservers", ["8.8.8.8", "4.4.4.4"]) -%}
{{sname}}-lxc-deploy:
  cloud.profile:
    - name: {{name}}
    - profile: {{data.get('profile', 'ms-{0}-dir-sratch'.format(data['target']))}}
    {% if name in ['makina-states'] %}
    - unless: test -e /var/lib/lxc/{{name}}/roots/etc/salt/pki/master/minions/makina-states
    {% else %}
    - unless: test -e {{cloudSettings.prefix}}/pki/master/minions/{{name}}
    {% endif %}
    - require:
      - mc_proxy: lxc-post-inst
      - mc_proxy: salt-cloud-predeploy
      - mc_proxy: salt-cloud-lxc-default-template
    - require_in:
      - mc_proxy: salt-cloud-postdeploy
      - mc_proxy: salt-cloud-lxc-devhost-hooks
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
{{sname}}-lxc-autostart:
  file.symlink:
    - name: /etc/lxc/auto/{{name}}.conf
    - target: /var/lib/lxc/{{name}}/config
    - makedirs: true
    - require:
      - cloud: {{sname}}-lxc-deploy
{% endmacro %}
{% for target, containers in services.lxcSettings.containers.items() %}
{%  for k, data in containers.items() -%}
{%    set data = data.copy() %}
{%    do data.update({'state_name': '{0}-{1}'.format(target, k)})%}
{%    do data.update({'target': target})%}
{{ lxc_container(data) }}
{%  endfor %}
{% endfor %}
