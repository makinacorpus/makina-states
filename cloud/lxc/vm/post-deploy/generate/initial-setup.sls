{% set compute_node_settings= salt['mc_cloud_compute_node.settings']() %}
{% set cloudSettings= salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
include:
  - makina-states.cloud.generic.hooks.generate
{% for target, vms in lxcSettings.vms.items() %}
{%  for vmname, data in vms.items() -%}
{% if compute_node_settings.targets[target].virt_types.lxc %}
{% set sname = '{0}-{1}'.format(target, vmname) %}
{% set cptslsname = '{1}/{0}/lxc/{2}/run-initial-setup'.format(
        target.replace('.', ''),
        cloudSettings.compute_node_sls_dir,
        vmname.replace('.', '')) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
c{{sname}}-lxc.computenode.sls-generator-for-setup:
  file.managed:
    - name: {{cptsls}}
    - user: root
    - mode: 750
    - makedirs: true
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
    - contents: |
              include:
                - makina-states.cloud.generic.hooks.vm
              {{sname}}-lxc-client-autostart-at-boot:
                salt.function:
                  - tgt: [{{target}}]
                  - expr_form: list
                  - name: cmd.run
                  - arg: [{{"'{0}'".format(
              "if [ ! -e /etc/lxc/auto ];then mkdir -p /etc/lxc/auto;fi;"
              "ln -sf /var/lib/lxc/{vmname}/config /etc/lxc/auto/{vmname}.conf".format(vmname=vmname))}}]
                  - watch:
                    - mc_proxy: cloud-generic-vm-pre-initial-setup-deploy
                  - watch_in:
                    - mc_proxy: cloud-generic-vm-post-initial-setup-deploy
              {{sname}}-lxc-sysadmin-user-initial-password:
                salt.function:
                  - tgt: [{{vmname}}]
                  - expr_form: list
                  - name: cmd.run
                  - watch:
                    - mc_proxy: cloud-generic-vm-pre-initial-setup-deploy
                  - watch_in:
                    - mc_proxy: cloud-generic-vm-post-initial-setup-deploy
                  - arg: ['if [ ! -e /.initialspasses ];then
                             for i in ubuntu root sysadmin;do
                               echo "${i}:{{data.password}}" | chpasswd && touch /.initialspasses;
                             done;
                          fi']
{%  endif %}
{% endfor %}
{% endfor %}
