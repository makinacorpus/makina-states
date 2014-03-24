{% set localsettings = salt['mc_localsettings.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set computenode_settings = salt['mc_cloud_compute_node.settings']() %}
include:
  - makina-states.cloud.generic.hooks.compute_node
{% for target, vm in computenode_settings.vm.items() %}
{% set cptslsname = '{1}/{0}/compute_node_hostfile'.format(target.replace('.', ''),
                                                           csettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, csettings.root) %}
{{sname}}-gen-lxc-host-postsetup:
  file.managed:
    - name: {{clxcsls}}
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-pre-grains-deploy
    - watch:
      - mc_proxy: cloud-generic-compute_node-post-post-deploy
    - user: root
    - makedirs: true
    - mode: 750
    - contents: |
                {% set domains = [] %}
                {%  for k, data in vm.items() -%}
                {% for name in data['domains'] %}
                {% do domains.append(name)%}
                {% if not name in domains%}
                avirt-{{name}}-makina-append-parent-etc.computenode.management:
                  file.blockreplace:
                    - name: /etc/hosts
                    - marker_start: '#-- start virt dns {{name}}:: DO NOT EDIT --'
                    - marker_end: '#-- end virt dns {{name}}:: DO NOT EDIT --'
                    - content: '# Vagrant vm: {{ name }} added this entry via local mount:'
                    - append_if_not_found: True
                    - backup: '.bak'
                    - show_changes: True
                amakina-parent-append-etc.computenode.accumulated-virt-{{name}}:
                  file.accumulated:
                    - watch_in:
                       - file: avirt-{{name}}-makina-append-parent-etc.computenode.management
                    - filename: /etc/hosts
                    - name: parent-hosts-append-accumulator-virt-{{ name }}-entries
                    - text: |
                            {{ data.ip }} {{ name }}
                virt-{{name}}-makina-prepend-parent-etc.computenode.management:
                  file.blockreplace:
                    - name: /etc/hosts
                    - marker_start: '#-- bstart virt dns {{name}}:: DO NOT EDIT --'
                    - marker_end: '#-- bend virt dns {{name}}:: DO NOT EDIT --'
                    - content: '# bVagrant vm: {{ name }} added this entry via local mount:'
                    - prepend_if_not_found: True
                    - backup: '.bak'
                    - show_changes: True
                makina-parent-prepend-etc.computenode.accumulated-virt-{{name}}:
                  file.accumulated:
                    - watch_in:
                       - file: virt-{{name}}-makina-prepend-parent-etc.computenode.management
                    - filename: /etc/hosts
                    - name: parent-hosts-prepend-accumulator-virt-{{ name }}-entries
                    - text: |
                            {{ data.ip }} {{ name }}
                {%raw%}{% if salt['mc_nodetypes.registry']()['is']['devhost'] %}{%endraw%}
                avirt-{{name}}-makina-append-parent-etc.computenode.management-devhost-touch:
                  file.touch:
                    - name: /etc/devhosts.{{name}}
                virt-{{name}}-makina-prepend-parent-etc.computenode.management-devhost:
                  file.blockreplace:
                    - name: /etc/devhosts.{{name}}
                    - marker_start: '#-- start devhost -- bstart virt dns {{name}}:: DO NOT EDIT --'
                    - marker_end: '#-- end devhost -- bend virt dns {{name}}:: DO NOT EDIT --'
                    - content: '# bVagrant vm: {{ name }} added this entry via local mount:'
                    - prepend_if_not_found: True
                    - backup: '.bak'
                    - show_changes: True
                    - watch:
                      - file: avirt-{{name}}-makina-append-parent-etc.computenode.management-devhost-touch
                makina-parent-prepend-etc.computenode.accumulated-virt-{{name}}-devhost:
                  file.accumulated:
                    - watch_in:
                       - file: virt-{{name}}-makina-prepend-parent-etc.computenode.management-devhost
                    - filename: /etc/devhosts.{{name}}
                    - name: parent-hosts-prepend-accumulator-virt-{{ name }}-entries
                    - text: |
                            {{ localsettings.devhost_ip }} {{ name }}
                {%raw%}{% endif %}{%endraw%}
                {%endif %}
                {%endfor%}
                {%endfor%}
{%  endfor %}
{% endfor %}
