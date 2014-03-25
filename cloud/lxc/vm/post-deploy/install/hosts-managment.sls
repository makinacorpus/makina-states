{% set compute_node_settings = salt['mc_cloud_compute_node.settings']() %}
{% set cloudSettings= salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
include:
  - makina-states.cloud.generic.hooks.vm

{% for target, vms in lxcSettings.vms.items() %}
{%  for vmname, data in vms.items() -%}
{% set sname = '{0}-{1}'.format(target, vmname) %}
{% if salt['mc_nodetypes.registry']()['is']['devhost'] %}
{% if compute_node_settings.targets[target].virt_types.lxc %}
{% set cptslsname = '{1}/{0}/lxc/{2}/contaner_hostfile'.format(
        target.replace('.', ''),
        cloudSettings.compute_node_sls_dir,
        vmname.replace('.', '')) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
c{{sname}}-lxc.computenode.sls-generator-for-hostnode-inst:
  salt.state:
    - tgt: [{{vmname}}]
    - expr_form: list
    - sls: {{cptslsname.replace('/', '.')}}
    - concurrent: True
    - watch:
      - mc_proxy: cloud-{{vmname}}-generic-vm-pre-hostsfiles-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-hostsfiles-deploy
{% endif %}
{% else %}
c{{sname}}-lxc.computenode.sls-generator-for-hostnode-inst:
  mc_proxy.hook: []
{% endif %}
{% endfor %}
{% endfor %}
