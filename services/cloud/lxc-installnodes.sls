{% import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% set cloudSettings= services.cloudSettings %}
{% set lxcSettings = services.lxcSettings %}
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
      - salt: {{data.target}}-lxc-client-install
      - file: {{sname}}-lxc-hosts-sls-generator-for-hostnode
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
{{sname}}-lxc-client-restart:
  salt.function:
    - tgt: [{{data.target}}]
    - expr_form: list
    - name: cmd.run
    - arg: [{{"'{0}'".format(
"if [ ! -e /etc/lxc/auto ];then mkdir -p /etc/lxc/auto;fi;"
"ln -sf /var/lib/lxc/{sname}/config /etc/lxc/auto/{sname}.conf".format(
            sname=sname))}}]
    - require:
      - cloud: {{sname}}-lxc-deploy
{% set lxcslsname = 'hosts-lxc-{0}'.format(sname.replace('.', '')) %}
{% if data['mode'] == 'mastersalt' %}
{% set lxcsls = '{1}/{0}.sls'.format(lxcslsname, saltmac.msaltRoot) %}
{% else %}
{% set lxcsls = '{1}/{0}.sls'.format(lxcslsname, saltmac.saltRoot) %}
{% endif %}
{{sname}}-lxc-hosts-sls-generator-for-hostnode:
  file.managed:
    - name: {{lxcsls}}
    - user: root
    - mode: 750
    - contents: |
                alxc-{{sname}}-makina-append-parent-etc-hosts-management:
                  file.blockreplace:
                    - name: /etc/hosts
                    - marker_start: '#-- start lxc dns {{sname}}:: DO NOT EDIT --'
                    - marker_end: '#-- end lxc dns {{sname}}:: DO NOT EDIT --'
                    - content: '# Vagrant vm: {{ sname }} added this entry via local mount:'
                    - append_if_not_found: True
                    - backup: '.bak'
                    - show_changes: True
                amakina-parent-append-etc-hosts-accumulated-lxc-{{sname}}:
                  file.accumulated:
                    - require_in:
                       - file: alxc-{{sname}}-makina-append-parent-etc-hosts-management
                    - filename: /etc/hosts
                    - name: parent-hosts-append-accumulator-lxc-{{ sname }}-entries
                    - text: |
                            {{ data.ip }} {{ name }}
                lxc-{{sname}}-makina-prepend-parent-etc-hosts-management:
                  file.blockreplace:
                    - name: /etc/hosts
                    - marker_start: '#-- bstart lxc dns {{sname}}:: DO NOT EDIT --'
                    - marker_end: '#-- bend lxc dns {{sname}}:: DO NOT EDIT --'
                    - content: '# bVagrant vm: {{ sname }} added this entry via local mount:'
                    - prepend_if_not_found: True
                    - backup: '.bak'
                    - show_changes: True
                makina-parent-prepend-etc-hosts-accumulated-lxc-{{sname}}:
                  file.accumulated:
                    - require_in:
                       - file: lxc-{{sname}}-makina-prepend-parent-etc-hosts-management
                    - filename: /etc/hosts
                    - name: parent-hosts-prepend-accumulator-lxc-{{ sname }}-entries
                    - text: |
                            {{ data.ip }} {{ name }}
                {% if nodetypes.registry.is.devhost %}
                alxc-{{sname}}-makina-append-parent-etc-hosts-management-devhost-touch:
                  file.touch:
                    - name: /etc/devhosts.{{name}}
                lxc-{{sname}}-makina-prepend-parent-etc-hosts-management-devhost:
                  file.blockreplace:
                    - name: /etc/devhosts.{{name}}
                    - marker_start: '#-- start devhost -- bstart lxc dns {{sname}}:: DO NOT EDIT --'
                    - marker_end: '#-- end devhost -- bend lxc dns {{sname}}:: DO NOT EDIT --'
                    - content: '# bVagrant vm: {{ sname }} added this entry via local mount:'
                    - prepend_if_not_found: True
                    - backup: '.bak'
                    - show_changes: True
                    - require:
                      - file: alxc-{{sname}}-makina-append-parent-etc-hosts-management-devhost-touch
                makina-parent-prepend-etc-hosts-accumulated-lxc-{{sname}}-devhost:
                  file.accumulated:
                    - require_in:
                       - file: lxc-{{sname}}-makina-prepend-parent-etc-hosts-management-devhost
                    - filename: /etc/devhosts.{{name}}
                    - name: parent-hosts-prepend-accumulator-lxc-{{ sname }}-entries
                    - text: |
                            {{ localsettings.settings.devhost_ip }} {{ name }}
                {% endif %}
  salt.state:
    - tgt: [{{data.target}}]
    - expr_form: list
    - sls: {{lxcslsname}}
    - concurrent: True

{{sname}}-lxc-sysadmin-user-initial-password:
  salt.function:
    - tgt: [{{name}}]
    - expr_form: list
    - name: cmd.run
    - timeout: 120
    - arg: ['if [ ! -e /.initialspass ];then echo "sysadmin:a{{data.password}}" | chpasswd && touch /.initialspass;fi']

{% endmacro %}

{% for target, containers in services.lxcSettings.containers.items() %}
{%  for k, data in containers.items() -%}
{%    set data = data.copy() %}
{%    do data.update({'state_name': '{0}-{1}'.format(target, k)})%}
{%    do data.update({'target': target})%}
{{ lxc_container(data) }}
{%  endfor %}
{{target}}-lxc-client-install:
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls: makina-states.services.cloud.lxc-node
    - concurrent: True
{% endfor %}

