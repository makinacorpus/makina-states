{% set cloudSettings= salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}

include:
  - makina-states.services.cloud.lxc.hooks

{% for target, vms in lxcSettings.vms.items() %}
{%  for k, data in vms.items() -%}
{%    set data = data.copy() %}
{%    do data.update({'state_name': '{0}-{1}'.format(target, k)})%}
{%    do data.update({'target': target})%}
{% set sname = data.get('state_name', data['name']) %}
{% set name = data['name'] %}
{% if salt['mc_nodetypes.registry']()['is']['devhost'] %}
{% set clxcslsname = 'lxc.computenode.{0}-vm'.format(sname.replace('.', '')) %}
{% set clxcsls = '{1}/{0}.sls'.format(clxcslsname, cloudSettings.root) %}
c{{sname}}-lxc.computenode.sls-generator-for-hostnode:
  file.managed:
    - name: {{clxcsls}}
    - user: root
    - mode: 750
    - makedirs: true
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
                            {{ data.gateway }} {{ grains['id'] }}
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
                            {{ data.gateway }} {{ grains['id'] }}
  salt.state:
    - tgt: [{{data.name}}]
    - expr_form: list
    - sls: {{clxcslsname.replace('/', '.')}}
    - concurrent: True
    - watch:
      - file: c{{sname}}-lxc.computenode.sls-generator-for-hostnode
      - mc_proxy: {{sname}}-lxc-deploy-end-hook
    - watch_in:
      - mc_proxy: {{sname}}-lxc-deploy-pre-initial-highstate
{% else %}
c{{sname}}-lxc.computenode.sls-generator-for-hostnode:
  mc_proxy.hook: []
{% endif %}
{% endfor %}
{% endfor %}
