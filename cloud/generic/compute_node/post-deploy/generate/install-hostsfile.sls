{% set localsettings = salt['mc_localsettings.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
include:
  - makina-states.cloud.generic.hooks.generate
{% for target in compute_node_settings.targets %}
{% set cptslsname = '{1}/{0}/compute_node_hostfile'.format(target.replace('.', ''),
                                                           cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{% set rcptslsname = '{1}/{0}/run-compute_node_hostfile'.format(target.replace('.', ''),
                                                           cloudSettings.compute_node_sls_dir) %}
{% set rcptsls = '{1}/{0}.sls'.format(rcptslsname, cloudSettings.root) %}
{{target}}-cloud-generic-inst-host-postsetup-gen-run:
  file.managed:
    - name: {{rcptsls}}
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
    - user: root
    - makedirs: true
    - mode: 750
    - contents: |
                include:
                  - makina-states.cloud.generic.hooks.compute_node
                {{target}}-cloud-generic-inst-host-postsetup-inst:
                  salt.state:
                    - tgt: [{{target}}]
                    - expr_form: list
                    - sls: {{cptslsname.replace('/', '.')}}
                    - concurrent: True
                    - watch:
                      - mc_proxy: cloud-generic-compute_node-pre-hostsfiles-deploy
                    - watch_in:
                      - mc_proxy: cloud-generic-compute_node-post-hostsfiles-deploy
{{target}}-cloud-generic-inst-host-postsetup-gen:
  file.managed:
    - name: {{cptsls}}
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
    - user: root
    - makedirs: true
    - mode: 750
    - contents: |
                {% set domains = [] %}
                {% set tdata = salt['mc_cloud_compute_node.get_settings_for_target'](target) %}
                {% for vmidname, data in tdata.vms.items() -%}
                {% for vmname in data['domains'] %}
                {% set sname = '{0}-{1}'.format(target, vmname) %}
                {% if not vmname in domains%}
                {% do domains.append(vmname)%}
                avirt-{{sname}}-makina-append-parent-etc.computenode.management:
                  file.blockreplace:
                    - name: /etc/hosts
                    - marker_start: '#-- start virt dns {{vmname}}:: DO NOT EDIT --'
                    - marker_end: '#-- end virt dns {{vmname}}:: DO NOT EDIT --'
                    - content: '# Vagrant vm: {{vmname}} added this entry via local mount:'
                    - append_if_not_found: True
                    - backup: '.bak'
                    - show_changes: True
                amakina-parent-append-etc.computenode.accumulated-virt-{{sname}}:
                  file.accumulated:
                    - watch_in:
                       - file: avirt-{{sname}}-makina-append-parent-etc.computenode.management
                    - filename: /etc/hosts
                    - name: parent-hosts-append-accumulator-virt-{{sname}}-entries
                    - text: |
                            {{ data.ip }} {{vmname}}
                virt-{{sname}}-makina-prepend-parent-etc.computenode.management:
                  file.blockreplace:
                    - name: /etc/hosts
                    - marker_start: '#-- bstart virt dns {{vmname}}:: DO NOT EDIT --'
                    - marker_end: '#-- bend virt dns {{vmname}}:: DO NOT EDIT --'
                    - content: '# bVagrant vm: {{vmname}} added this entry via local mount:'
                    - prepend_if_not_found: True
                    - backup: '.bak'
                    - show_changes: True
                makina-parent-prepend-etc.computenode.accumulated-virt-{{sname}}:
                  file.accumulated:
                    - watch_in:
                       - file: virt-{{sname}}-makina-prepend-parent-etc.computenode.management
                    - filename: /etc/hosts
                    - name: parent-hosts-prepend-accumulator-virt-{{sname}}-entries
                    - text: |
                            {{ data.ip }} {{vmname}}
                {%raw%}{% if salt['mc_nodetypes.registry']()['is']['devhost'] %}{%endraw%}
                avirt-{{sname}}-makina-append-parent-etc.computenode.management-devhost-touch:
                  file.touch:
                    - name: /etc/devhosts.{{vmname}}
                virt-{{sname}}-makina-prepend-parent-etc.computenode.management-devhost:
                  file.blockreplace:
                    - name: /etc/devhosts.{{vmname}}
                    - marker_start: '#-- start devhost -- bstart virt dns {{vmname}}:: DO NOT EDIT --'
                    - marker_end: '#-- end devhost -- bend virt dns {{vmname}}:: DO NOT EDIT --'
                    - content: '# bVagrant vm: {{vmname}} added this entry via local mount:'
                    - prepend_if_not_found: True
                    - backup: '.bak'
                    - show_changes: True
                    - watch:
                      - file: avirt-{{sname}}-makina-append-parent-etc.computenode.management-devhost-touch
                makina-parent-prepend-etc.computenode.accumulated-virt-{{sname}}-devhost:
                  file.accumulated:
                    - watch_in:
                       - file: virt-{{sname}}-makina-prepend-parent-etc.computenode.management-devhost
                    - filename: /etc/devhosts.{{vmname}}
                    - name: parent-hosts-prepend-accumulator-virt-{{sname}}-entries
                    - text: |
                            {{ localsettings.devhost_ip }} {{vmname}}
                {%raw%}{% endif %}{%endraw%}
                {%endif %}
                {%endfor%}
                {%endfor%}
{% endfor %}
