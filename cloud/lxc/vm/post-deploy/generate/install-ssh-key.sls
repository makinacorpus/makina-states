{% set saltreg = mc_salt['mc_controllers.settings']() %}
include:
  - makina-states.cloud.generic.hooks.vm
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
{% for target, vms in lxcSettings.vms.items() %}
{% for vmname, data in vms.items() %}
{% set sname = data.get('state_name', '{0}-{1}'.format(target, k) %}
{% set cptslsname = '{1}/{0}/{2}/container_ssh_key'.format(
        target.replace('.', ''),
        csettings.vms_sls_dir,
        vmname.replace('.', '')) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, csettings.root) %}
{{sname}}-lxc.vm-install-ssh-key:
  file.managed:
    - name: {{cptsls}}
    - user: root
    - mode: 750
    - makedirs: true
    - watch:
      - mc_proxy: cloud-generic-vm-pre-install-ssh-key
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-pre-install-ssh-key
    - contents: |
                inskey:
                  ssh_auth.present:
                    - source: salt://rootkey.pub
                    - user: root
{% endfor %}
{% endfor %}
