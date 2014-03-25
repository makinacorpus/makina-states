{% set saltreg = mc_salt['mc_controllers.settings']() %}
include:
  - makina-states.cloud.generic.hooks.vm
  - makina-states.cloud.generic.gensssh
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
{% for target, vms in lxcSettings.vms.items() %}
{% for vmname, data in vms.iteritems() %}
{% set sname = data.get('state_name', '{0}-{1}'.format(target, k) %}
{% set cptslsname = '{1}/{0}/container_ssh_key'.format(
        target.replace('.', ''),
        csettings.vms_sls_dir,
        vmname.replace('.', '')) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, csettings.root) %}
{{sname}}-lxc.vm-install-ssh-key:
  salt.state:
    - tgt: [{{vmname}}]
    - expr_form: list
    - sls: {{cptslsname.replace('/', '.')}}
    - concurrent: True
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-pre-install-ssh-key
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-post-install-ssh-key
{% endfor %}
{% endfor %}
