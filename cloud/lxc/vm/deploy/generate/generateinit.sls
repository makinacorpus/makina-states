include:
  - makina-states.cloud.generic.hooks.vm
{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% for target, vms in lxcSettings.vms.items() %}
{% if compute_node_settings.targets[target].virt_types.lxc %}
{%  for vmname, data in vms.items() -%}
{% set cptslsnamepref = '{1}/{0}/lxc/{2}'.format(target.replace('.', ''),
                                           cloudSettings.compute_node_sls_dir,
                                           vmname.replace('.', '')) %}
{{target}}-{{vmname}}-gen-lxc-init:
  file.managed:
    - name: {{cloudSettings.root}}/{{cptslsnamepref}}/init.sls
    - makedirs: true
    - mode: 750
    - watch:
      - mc_proxy: cloud-generic-vm-pre-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-pre-deploy
    - user: root
    - group: editor
    - contents: |
              include:
                - makina-states.cloud.lxc.controller.install
                - makina-states.cloud.lxc.compute_node.install
                - {{cptslsnamepref.replace('/', '.')}}.run-grains
                - {{cptslsnamepref.replace('/', '.')}}.run-spawn
                - {{cptslsnamepref.replace('/', '.')}}.run-initial-highstate
                - {{cptslsnamepref.replace('/', '.')}}.run-initial-setup
                - {{cptslsnamepref.replace('/', '.')}}.run-hosts-managment
                - {{cptslsnamepref.replace('/', '.')}}.run-install-ssh-key
{%  endfor %}
{%  endif %}
{% set gcptslsnamepref = '{1}/{0}/lxc'.format(target.replace('.', ''),
                                           cloudSettings.compute_node_sls_dir,
                                           vmname) %}
{{target}}-gen-lxc-vms-init:
  file.managed:
    - name: {{cloudSettings.root}}/{{gcptslsnamepref}}/init.sls
    - makedirs: true
    - mode: 750
    - watch:
      - mc_proxy: cloud-generic-vm-pre-deploy
    - user: root
    - group: editor
    - contents: |
              include:
                - makina-states.cloud.lxc.controller.install
                - makina-states.cloud.lxc.compute_node.install
                {%  for vmname, data in vms.items() -%}
                - {{gcptslsnamepref.replace('/', '.')}}.{{vmname.replace('.', '')}}
                {% endfor %}
{% endfor %}
