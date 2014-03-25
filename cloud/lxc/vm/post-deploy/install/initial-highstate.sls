{% set compute_node_settings = salt['mc_cloud_controller.settings']() %}
{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
include:
  - makina-states.hooks.generic.hooks.vm
{% for target, vms in lxcSettings.vms.items() %}
{%  for vmname, data in vms.items() -%}
{% if compute_node_settings.targets[target].virt_types.lxc %}
{% set sname = '{0}-{1}'.format(target, vmname) %}
{% set salts = cloudSettings.root %}
{% set msr = '{0}/makina-states'.format(salts) %}
c{{sname}}-lxc-initial-highstate:
  cmd.run:
    - name: ssh {{vmname}} "{{msr}}/_scripts/boot-salt.sh --initial-highstate"
    - user: root
    - watch:
      - mc_proxy: cloud-{{vmname}}-generic-vm-pre-initial-highstate-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-initial-highstate-deploy
{% endif %}
{% endfor %}
{% endfor %}
