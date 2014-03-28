include:
  - makina-states.cloud.generic.hooks.generate
{# generate an init file callable on a per compute node basis #}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% for target, data in compute_node_settings['targets'].items() %}
{# authorize root from cloudcontroller to connect via ssh on targets #}
{% set cptslsnamepref = '{1}/{0}/'.format(target.replace('.', ''),
                                         cloudSettings.compute_node_sls_dir) %}
{% set cptsls = '{1}/{0}/lxc-compute_node.sls'.format(cptslsnamepref, cloudSettings.root) %}
{{target}}-gen-lxc-compute_node-init:
  file.managed:
    - name: {{cptsls}}
    - makedirs: true
    - mode: 750
    - user: root
    - group: {{localsettings.group}}
    - contents: |
              include:
                - {{cptslsnamepref.replace('/', '.')}}lxc.run-computenode_lxc_grains
                - {{cptslsnamepref.replace('/', '.')}}lxc.run-images-templates
                - {{cptslsnamepref.replace('/', '.')}}lxc.run-installation
                {% if salt['mc_nodetypes.registry']().is.devhost %}- makina-states.cloud.lxc.compute_node.devhost.install{% endif %}
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
{% endfor %}
