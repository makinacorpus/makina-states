include:
  - makina-states.cloud.generic.hooks.generate
{% set localsettings = salt['mc_localsettings.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% for target, vmnames in lxcSettings.vms.items() %}
{% if 'lxc' in compute_node_settings.targets[target].virt_types %}
{% set gcptslsnamepref = '{1}/{0}/lxc'.format(target.replace('.', ''),
                                           cloudSettings.compute_node_sls_dir,
                                           vmname) %}
{% set slspref = gcptslsnamepref.replace('/', '.')%}
{{target}}-gen-run-compute-node:
  file.managed:
    - name: {{cloudSettings.root}}/{{gcptslsnamepref}}/run-compute_node.sls
    - makedirs: true
    - mode: 750
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
    - user: root
    - group: {{localsettings.group}}
    - contents: |
                {%raw%}{# WARNING THIS STATE FILE IS GENERATED #}{%endraw%}
                include:
                {% for sls in ['run-compute_node_lxc-installation',
                               'run-compute_node_images-templates',
                               'run-compute_node_lxc-grains', ] %}
                  - {{slspref}}.{{sls}}
                {% endfor %}
                {% if salt['mc_nodetypes.registry']().is.devhost %}
                  - makina-states.cloud.lxc.compute_node.devhost.install
                {% endif %}
{{target}}-gen-lxc-vms-init:
  file.managed:
    - name: {{cloudSettings.root}}/{{gcptslsnamepref}}/init.sls
    - makedirs: true
    - mode: 750
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
    - user: root
    - group: {{localsettings.group}}
    - contents: |
                {%raw%}{# WARNING THIS STATE FILE IS GENERATED #}{%endraw%}
                include:
                  - {{gcptslsnamepref.replace('/', '.')}}.run-compute_node
                  {%  for vmname in vmnames -%}
                  - {{gcptslsnamepref.replace('/', '.')}}.{{vmname.replace('.', '')}}
                  {% endfor %}
{%  endif %}
{%  endfor %}
