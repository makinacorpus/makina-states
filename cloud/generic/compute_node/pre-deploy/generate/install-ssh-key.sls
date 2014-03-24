{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set computenodeSettings = salt['mc_cloud_compute_node.settings']() %}
{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
include:
  - makina-states.cloud.generic.genssh
{% for target, vm in lxcSettings.vm.items() %}
{# authorize root from cloudcontroller to connect via ssh on targets #}
{% set slsname = 'lxc.compute_node.install-{0}-ssh-key'.format(
                   target.replace('.', '_')) %}
{% set saltr = cloudSettings.root %}
{% set slspath = '{0}/{1}.sls'.format(saltr, slsname) %}
{{target}}-inst-lxc-host-install-ssh-key:
  file.managed:
    - name: {{slspath}}
    - watch:
      - file: {{target}}-lxc-root-keygen
    - user: root
    - mode: 750
    - makedirs: true
    - contents: |
                inskey:
                  ssh_auth.present:
                    - source: salt://rootpubkey.pub
                    - user: root
{% endfor %}
