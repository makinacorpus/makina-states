{% import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{% import "makina-states/_macros/nodetypes.jinja" as nodetypes with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% set cloudSettings= services.cloudSettings %}
{% set lxcSettings = services.lxcSettings %}
include:
  - makina-states.services.cloud.lxc.hooks

{% for target, containers in services.lxcSettings.containers.items() %}
{%  for k, data in containers.items() -%}
{%    set data = data.copy() %}
{%    do data.update({'state_name': '{0}-{1}'.format(target, k)})%}
{%    do data.update({'target': target})%}
{%    set sname = data.get('state_name', data['name']) %}
{%    set name = data['name'] %}
{%    set lxcslsname = 'lxc.computenode.{0}'.format(sname.replace('.', '')) %}
{%    if data['mode'] == 'mastersalt' %}
{%        set lxcsls = '{1}/{0}.sls'.format(lxcslsname, saltmac.msaltRoot) %}
{%    else %}
{%        set lxcsls = '{1}/{0}.sls'.format(lxcslsname, saltmac.saltRoot) %}
{%    endif %}
{{sname}}-lxc-host-postsetup:
  file.managed:
    - name: {{lxcsls}}
    - watch:
      - mc_proxy: {{sname}}-lxc-deploy-end-hook
    - user: root
    - makedirs: true
    - mode: 750
    - contents: |
                alxc-{{sname}}-makina-append-parent-etc.computenode.management:
                  file.blockreplace:
                    - name: /etc/hosts
                    - marker_start: '#-- start lxc dns {{sname}}:: DO NOT EDIT --'
                    - marker_end: '#-- end lxc dns {{sname}}:: DO NOT EDIT --'
                    - content: '# Vagrant vm: {{ sname }} added this entry via local mount:'
                    - append_if_not_found: True
                    - backup: '.bak'
                    - show_changes: True
                amakina-parent-append-etc.computenode.accumulated-lxc-{{sname}}:
                  file.accumulated:
                    - watch_in:
                       - file: alxc-{{sname}}-makina-append-parent-etc.computenode.management
                    - filename: /etc/hosts
                    - name: parent-hosts-append-accumulator-lxc-{{ sname }}-entries
                    - text: |
                            {{ data.ip }} {{ name }}
                lxc-{{sname}}-makina-prepend-parent-etc.computenode.management:
                  file.blockreplace:
                    - name: /etc/hosts
                    - marker_start: '#-- bstart lxc dns {{sname}}:: DO NOT EDIT --'
                    - marker_end: '#-- bend lxc dns {{sname}}:: DO NOT EDIT --'
                    - content: '# bVagrant vm: {{ sname }} added this entry via local mount:'
                    - prepend_if_not_found: True
                    - backup: '.bak'
                    - show_changes: True
                makina-parent-prepend-etc.computenode.accumulated-lxc-{{sname}}:
                  file.accumulated:
                    - watch_in:
                       - file: lxc-{{sname}}-makina-prepend-parent-etc.computenode.management
                    - filename: /etc/hosts
                    - name: parent-hosts-prepend-accumulator-lxc-{{ sname }}-entries
                    - text: |
                            {{ data.ip }} {{ name }}
                {% if nodetypes.registry.is.devhost %}
                alxc-{{sname}}-makina-append-parent-etc.computenode.management-devhost-touch:
                  file.touch:
                    - name: /etc/devhosts.{{name}}
                lxc-{{sname}}-makina-prepend-parent-etc.computenode.management-devhost:
                  file.blockreplace:
                    - name: /etc/devhosts.{{name}}
                    - marker_start: '#-- start devhost -- bstart lxc dns {{sname}}:: DO NOT EDIT --'
                    - marker_end: '#-- end devhost -- bend lxc dns {{sname}}:: DO NOT EDIT --'
                    - content: '# bVagrant vm: {{ sname }} added this entry via local mount:'
                    - prepend_if_not_found: True
                    - backup: '.bak'
                    - show_changes: True
                    - watch:
                      - file: alxc-{{sname}}-makina-append-parent-etc.computenode.management-devhost-touch
                makina-parent-prepend-etc.computenode.accumulated-lxc-{{sname}}-devhost:
                  file.accumulated:
                    - watch_in:
                       - file: lxc-{{sname}}-makina-prepend-parent-etc.computenode.management-devhost
                    - filename: /etc/devhosts.{{name}}
                    - name: parent-hosts-prepend-accumulator-lxc-{{ sname }}-entries
                    - text: |
                            {{ localsettings.settings.devhost_ip }} {{ name }}
                {% endif %}
  salt.state:
    - tgt: [{{data.target}}]
    - expr_form: list
    - sls: {{lxcslsname.replace('/', '.')}}
    - concurrent: True
    - watch:
      - file: {{sname}}-lxc-host-postsetup
      - mc_proxy: {{sname}}-lxc-deploy-end-hook
    - watch_in:
      - mc_proxy: {{target}}-target-post-setup-hook
{%  endfor %}
{% endfor %}
