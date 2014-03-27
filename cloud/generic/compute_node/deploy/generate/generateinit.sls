include:
  - makina-states.cloud.generic.hooks.compute_node
{# generate an init file callable on a per compute node basis #}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% for target, data in compute_node_settings['targets'].items() %}
{# authorize root from cloudcontroller to connect via ssh on targets #}
{% set cptslsnamepref = '{1}/{0}/'.format(target.replace('.', ''),
                                         cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}/init.sls'.format(cptslsnamepref, cloudSettings.root) %}
{{target}}-gen-init:
  file.managed:
    - name: {{cptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: editor
    - contents: |
              include:
                {# generic compute node part #}
                - makina-states.cloud.generic.controller.install
                - {{cptslsnamepref.replace('/', '.')}}run-compute_node_ssh_key
                - {{cptslsnamepref.replace('/', '.')}}run-compute_node_grains
                - {{cptslsnamepref.replace('/', '.')}}run-compute_node_firewall
                - {{cptslsnamepref.replace('/', '.')}}run-compute_node_reverseproxy
                - {{cptslsnamepref.replace('/', '.')}}run-compute_node_hostfile
                {% for virt_type in data.virt_types -%}
                {%- set cvtcptslsname = '{1}/{0}/{2}-controller'.format(target.replace('.', ''),
                                           cloudSettings.compute_node_sls_dir, virt_type) %}
                {%- set cvtcptslsname = '{1}/{0}/{2}-compute_node'.format(target.replace('.', ''),
                                           cloudSettings.compute_node_sls_dir, virt_type) %}
                {%- set vtcptslsname = '{1}/{0}/{2}'.format(target.replace('.', ''),
                                           cloudSettings.compute_node_sls_dir, virt_type) %}
                {%raw%}{% if salt['mc_cloud.registry']().is['{%endraw%}{{virt_type}}{%raw%}'] %}{%endraw%}
                - makina-states.cloud.{{virt_type}}.controller.install
                - {{cvtcptslsname.replace('/', '.')}}
                - {{vtcptslsname.replace('/', '.')}}
                {%raw%}{%endif %}{%endraw%}
                {%- endfor %}
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-deploy
{% endfor %}
