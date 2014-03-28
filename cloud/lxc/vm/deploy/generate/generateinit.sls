include:
  - makina-states.cloud.generic.hooks.generate
{% set localsettings = salt['mc_localsettings.settings']() %}
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% for target, vmnames in lxcSettings.vms.items() %}
{% if 'lxc' in compute_node_settings.targets[target].virt_types %}
{%  for vmname in vmnames -%}
{% set cptslsnamepref = '{1}/{0}/lxc/{2}'.format(target.replace('.', ''),
                                           cloudSettings.compute_node_sls_dir,
                                           vmname.replace('.', '')) %}
{% set slspref = cptslsnamepref.replace('/', '.')%}
{% set slss = ['run-container_spawn',
               'run-container_grains',
               'run-container_initial-highstate',
               'run-container_initial-setup',
               'run-container_install-ssh-key', ] %}
{% if salt['mc_nodetypes.registry']()['is']['devhost'] %}
{% do slss.append('run-container_hosts-managment') %}
{% endif %}
{{target}}-{{vmname}}-gen-lxc-init:
  file.managed:
    - name: {{cloudSettings.root}}/{{cptslsnamepref}}/init.sls
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
                {% for sls in slss  %}
                  - {{slspref}}.{{sls}}
                {% endfor %}
{%  endfor %}
{%  endif %}
{% endfor %}
