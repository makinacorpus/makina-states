include:
  - makina-states.cloud.generic.hooks.generate
{% set localsettings = salt['mc_localsettings.settings']() %}
{# generate an init file callable on a per compute node basis #}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% for target, data in compute_node_settings['targets'].items() %}
{# authorize root from cloudcontroller to connect via ssh on targets #}
{% set cptslsnamepref = '{1}/{0}/'.format(target.replace('.', ''),
                                         cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}/init.sls'.format(cptslsnamepref, cloudSettings.root) %}
{% set ccptsls = '{1}/{0}/run-compute_node.sls'.format(cptslsnamepref, cloudSettings.root) %}
{% set contcptsls = '{1}/{0}/controller.sls'.format(cptslsnamepref, cloudSettings.root) %}
{{target}}-gen-controller_init:
  file.managed:
    - name: {{contcptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: {{localsettings.group}}
    - contents: |
                include:
                  - makina-states.cloud.generic.controller.install
                  {% for virt_type in data.virt_types %}
                  - makina-states.cloud.{{virt_type}}.controller.install
                  {% endfor %}
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end


{{target}}-gen-compute_node_init:
  file.managed:
    - name: {{ccptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: {{localsettings.group}}
    - contents: |
                include:
                  - {{cptslsnamepref.replace('/', '.')}}run-compute_node_ssh_key
                  - {{cptslsnamepref.replace('/', '.')}}run-compute_node_grains
                  - {{cptslsnamepref.replace('/', '.')}}run-compute_node_firewall
                  - {{cptslsnamepref.replace('/', '.')}}run-compute_node_reverseproxy
                  - {{cptslsnamepref.replace('/', '.')}}run-compute_node_hostfile
                  {% for virt_type in data.virt_types %}
                  {% set cvtcptslsname = '{1}/{0}/{2}/run-compute_node'.format(
                        target.replace('.', ''), cloudSettings.compute_node_sls_dir, virt_type) %}
                  - {{cvtcptslsname.replace('/', '.')}}
                  {% endfor %}
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end


{{target}}-gen-init:
  file.managed:
    - name: {{cptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: {{localsettings.group}}
    - contents: |
                include:
                  - {{cptslsnamepref.replace('/', '.')}}controller
                  - {{cptslsnamepref.replace('/', '.')}}run-compute_node
                  {% for virt_type in data.virt_types %}
                  {% set vtcptslsname = '{1}/{0}/{2}'.format(
                        target.replace('.', ''), cloudSettings.compute_node_sls_dir, virt_type) %}
                  - {{cptslsnamepref.replace('/', '.')}}{{virt_type}}
                  {% endfor %}
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
{% endfor %}
