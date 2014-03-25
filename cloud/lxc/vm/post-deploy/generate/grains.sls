{% set compute_node_settings= salt['mc_cloud_controller.settings']() %}
{% set cloudSettings= salt['mc_cloud.settings']() %}
include:
  - makina-states.cloud.generic.hooks.vm
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
{% for target, vms in lxcSettings.vms.items() %}
{% for vmname, data in vms.items() %}
{% set sname = '{0}-{1}'.format(target, vmname)%}
{% set cptslsname = '{1}/{0}/lxc/{2}/container_grains'.format(
        target.replace('.', ''),
        cloudSettings.compute_node_sls_dir,
        vmname.replace('.', '')) %}
{% set cptsls = '{1}/{0}.sls'.format(cptslsname, cloudSettings.root) %}
{{sname}}-lxc.vm-install-grains-gen:
  file.managed:
    - name: {{cptsls}}
    - user: root
    - mode: 750
    - makedirs: true
    - watch:
      - mc_proxy: cloud-generic-vm-pre-grains-deploy
    - watch_in:
      - mc_proxy: cloud-{{vmname}}-generic-vm-pre-grains-deploy
    - contents: |
        {{sname}}-run-grains:
          grains.present:
            - names:
              - makina-states.cloud.is.compute_node
              - makina-states.services.proxy.haproxy
              - makina-states.services.firewall.shorewall
              - makina-states.cloud.compute_node.has.firewall
            - value: true
        {{ sname }}-reload-grains:
          cmd.script:
            - source: salt://makina-states/_scripts/reload_grains.sh
            - template: jinja
            - watch:
              - grains: {{target}}-run-grains
{% endfor %}
{% endfor %}
