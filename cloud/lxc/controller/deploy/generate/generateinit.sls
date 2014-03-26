include:
  - makina-states.cloud.generic.hooks.compute_node
{# generate an init file callable on a per compute node basis #}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% for target, data in compute_node_settings['targets'].items() %}
{# authorize root from cloudcontroller to connect via ssh on targets #}
{% set cptslsnamepref = '{1}/{0}/'.format(target.replace('.', ''),
                                         cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}/lxc-controller.sls'.format(cptslsnamepref, cloudSettings.root) %}
{{target}}-gen-lxc-controller-init:
  file.managed:
    - name: {{cptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: editor
    - contents: |
              include:
                - makina-states.cloud.lxc.controller.install
    - watch:
      - mc_proxy: cloud-generic-compute_node-pre-deploy
    - watch_in:
      - mc_proxy: cloud-generic-compute_node-post-deploy
{% endfor %}
