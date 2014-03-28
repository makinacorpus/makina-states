{% set compute_node_settings= salt['mc_cloud_compute_node.settings']() %}
{% set cloudSettings= salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
include:
  - makina-states.cloud.generic.hooks.generate
{% for target, vms in lxcSettings.vms.items() %}
{% for vmname, data in vms.items() -%}
{% set sname = '{0}-{1}'.format(target, vmname) %}
{% if salt['mc_nodetypes.registry']()['is']['devhost'] %}
{% set cptslsname = '{1}/{0}/lxc/{2}/container_hostfile'.format(
        target.replace('.', ''),
        cloudSettings.compute_node_sls_dir,
        vmname.replace('.', '')) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{% set rcptslsname = '{1}/{0}/lxc/{2}/run-hosts-managment'.format(
        target.replace('.', ''),
        cloudSettings.compute_node_sls_dir,
        vmname.replace('.', '')) %}
{% set rcptsls = '{1}/{0}.sls'.format(rcptslsname, cloudSettings.root) %}
c{{sname}}-lxc.computenode.sls-generator-for-hostnode-gen:
  file.managed:
    - name: {{cptsls}}
    - user: root
    - mode: 750
    - makedirs: true
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
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
                            {{ data.gateway }} {{ target }} {{grains['id'] }}
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
                            {{ data.gateway }} {{ target }} {{grains['id'] }}
{{sname}}-run-lxc.vm-host-management-gen:
  file.managed:
    - name: {{rcptsls}}
    - user: root
    - mode: 750
    - makedirs: true
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
    - contents: |
            c{{sname}}-lxc.computenode.sls-generator-for-hostnode-inst:
              salt.state:
                - tgt: [{{vmname}}]
                - expr_form: list
                - sls: {{cptslsname.replace('/', '.')}}
                - concurrent: True
                - watch:
                  - mc_proxy: cloud-generic-vm-pre-hostsfiles-deploy
                - watch_in:
                  - mc_proxy: cloud-generic-vm-post-hostsfiles-deploy
{% else %}
c{{sname}}-lxc.computenode.sls-generator-for-hostnode:
  mc_proxy.hook: []
{% endif %}
{% endfor %}
{% endfor %}
