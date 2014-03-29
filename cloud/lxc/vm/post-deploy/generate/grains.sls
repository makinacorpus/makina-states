{% set compute_node_settings= salt['mc_cloud_controller.settings']() %}
{% set cloudSettings= salt['mc_cloud.settings']() %}
include:
  - makina-states.cloud.generic.hooks.generate
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
{% for target, vmnames in lxcSettings.vms.items() %}
{% for vmname in vmnames %}
{% set sname = '{0}-{1}'.format(target, vmname)%}
{% set cptslsname = '{1}/{0}/lxc/{2}/container_grains'.format(
        target.replace('.', ''),
        cloudSettings.compute_node_sls_dir,
        vmname.replace('.', '')) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{% set rcptslsname = '{1}/{0}/lxc/{2}/run-container_grains'.format(
        target.replace('.', ''),
        cloudSettings.compute_node_sls_dir,
        vmname.replace('.', '')) %}
{% set rcptsls = '{1}/{0}.sls'.format(rcptslsname, cloudSettings.root) %}
{{sname}}-lxc.vm-install-grains-gen-run:
  file.managed:
    - name: {{rcptsls}}
    - user: root
    - mode: 750
    - makedirs: true
    - watch:
      - mc_proxy: cloud-generic-generate
    - watch_in:
      - mc_proxy: cloud-generic-generate-end
    - contents: |
                {%raw%}{# WARNING THIS STATE FILE IS GENERATED #}{%endraw%}
                c{{sname}}-lxcgrains.computenode.sls-generator-for-hostnode-inst:
                  salt.state:
                    - tgt: [{{vmname}}]
                    - expr_form: list
                    - sls: {{cptslsname.replace('/', '.')}}
                    - concurrent: True
                    - watch:
                      - mc_proxy: cloud-generic-vm-pre-grains-deploy
                    - watch_in:
                      - mc_proxy: cloud-generic-vm-post-grains-deploy
{{sname}}-lxc.vm-install-grains-gen:
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
                {%raw%}{# WARNING THIS STATE FILE IS GENERATED #}{%endraw%}
                {{sname}}-run-grains:
                  grains.present:
                    - names:
                      - makina-states.cloud.is.vm
                      - makina-states.nodetypes.lxccontainer
                    - value: true
                {{ sname }}-reload-grains:
                  cmd.script:
                    - source: salt://makina-states/_scripts/reload_grains.sh
                    - template: jinja
                    - watch:
                      - grains: {{sname}}-run-grains
{% endfor %}
{% endfor %}
