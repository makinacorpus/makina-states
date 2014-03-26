{% set compute_node_settings= salt['mc_cloud_compute_node.settings']() %}
{% set cloudSettings= salt['mc_cloud.settings']() %}
include:
  - makina-states.cloud.generic.genssh
  - makina-states.cloud.generic.hooks.vm
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
{% for target, vms in lxcSettings.vms.items() %}
{% for vmname, data in vms.items() %}
{% if compute_node_settings.targets[target].virt_types.lxc %}
{% set sname = '{0}-{1}'.format(target, vmname) %}
{% set cptslsname = '{1}/{0}/lxc/{2}/container_ssh_key'.format(
        target.replace('.', ''),
        cloudSettings.compute_node_sls_dir,
        vmname.replace('.', '')) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{% set rcptslsname = '{1}/{0}/lxc/{2}/run-install-ssh-key'.format(
        target.replace('.', ''),
        cloudSettings.compute_node_sls_dir,
        vmname.replace('.', '')) %}
{% set rcptsls = '{1}/{0}.sls'.format(rcptslsname, cloudSettings.root) %}
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
                insdsakey:
                  ssh_auth.present:
                    - source: salt://{{cloudSettings.all_sls_dir}}/rootkey-dsa.pub
                    - user: root
                inskey:
                  ssh_auth.present:
                    - source: salt://{{cloudSettings.all_sls_dir}}/rootkey-rsa.pub
                    - user: root
{{sname}}-run-lxc.vm-install-ssh-key-gen:
  file.managed:
    - name: {{rcptsls}}
    - user: root
    - mode: 750
    - makedirs: true
    - watch:
      - mc_proxy: cloud-generic-vm-pre-install-ssh-key
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-pre-install-ssh-key
    - contents: |
          include:
            - makina-states.cloud.generic.hooks.vm
            - makina-states.cloud.generic.genssh
          {{sname}}-lxc.vm-install-ssh-key-inst:
            salt.state:
              - tgt: [{{vmname}}]
              - expr_form: list
              - sls: {{cptslsname.replace('/', '.')}}
              - concurrent: True
              - watch_in:
                - mc_proxy: cloud-{{vmname}}-generic-vm-pre-install-ssh-key
              - watch_in:
                - mc_proxy: cloud-{{vmname}}-generic-vm-post-install-ssh-key
{% endif %}
{% endfor %}
{% endfor %}
