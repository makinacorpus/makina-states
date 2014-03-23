{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% set cloudSettings = salt['mc_cloud_controller.settings']() %}
{% set lxcSettings = salt['mc_cloud_lxc.settings']() %}
include:
  - makina-states.services.cloud.lxc.hooks

{% for target, vm in lxcSettings.vm.items() %}
{# authorize root from cloudcontroller to connect via ssh on targets #}
{% set slsname = 'lxc.compute_node.install-{0}-ssh-key'.format(
            target.replace('.', '_')) %}
{% set saltr = cloudSettings.root %}
{% set slspath = '{0}/{1}.sls'.format(saltr, slsname) %}
{{target}}-lxc-root-keygen:
  cmd.run:
    - name: ssh-keygen -t dsa
    - user: root
    - unless: test -e /root/.ssh/id_dsa
  file.copy:
    - name: {{saltr}}/lxc.pub
    - source: /root/.ssh/id_dsa.pub
    - user: root
    - watch:
      - cmd: {{target}}-lxc-root-keygen

{{target}}-lxc-host-install-ssh-key:
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
                    - source: salt://lxc.pub
                    - user: root
  salt.state:
    - tgt: [{{target}}]
    - expr_form: list
    - sls: {{slsname.replace('/', '.')}}
    - concurrent: True
    - watch:
      - file: {{target}}-lxc-host-install-ssh-key
    - watch_in:
      - mc_proxy: salt-cloud-lxc-{{target}}-ssh-key
{{target}}-lxc-root-keygen-clean:
  file.absent:
    - name: {{saltr}}/lxc.pub
    - watch:
      - salt: {{target}}-lxc-host-install-ssh-key
{% endfor %}
