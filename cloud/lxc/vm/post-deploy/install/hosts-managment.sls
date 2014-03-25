{% set cloudSettings= salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
include:
  - makina-states.hooks.generic.hooks.vm

{% for target, vms in lxcSettings.vms.items() %}
{%  for vmname, data in vms.items() -%}
{% set sname = '{0}-{1}'.format(target, vmname) %}
{% if salt['mc_nodetypes.registry']()['is']['devhost'] %}
{% set cptslsname = '{1}/{0}/{2}/compute_node_hostfile'.format(
        target.replace('.', ''),
        csettings.vms_sls_dir,
        vmname.replace('.', '')) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, csettings.root) %}
c{{sname}}-lxc.computenode.sls-generator-for-hostnode-inst:
  salt.state:
    - tgt: [{{vmname}}]
    - expr_form: list
    - sls: {{cptslsname.replace('/', '.')}}
    - concurrent: True
    - watch:
      - mc_proxy: cloud-{{vmname}}-generic-vm-pre-vm-hostsfiles-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-vm-hostsfiles-deploy
{% else %}
c{{sname}}-lxc.computenode.sls-generator-for-hostnode:
  mc_proxy.hook: []
{% endif %}
{% endfor %}
{% endfor %}
