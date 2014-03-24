{% set saltreg = mc_salt['mc_controllers.settings']() %}
include:
  - makina-states.services.cloud.lxc.hooks
{% set cloudSettings = salt['mc_cloud.settings']() %}
{% set lxcSettings= salt['mc_cloud_lxc.settings']() %}
{% for target, vms in lxcSettings.vms.items() %}
{% for k, data in vms.iteritems() %}
{# authorize root from cloudcontroller to connect via ssh on targets #}
{% set name = data.name %}
{%    set data = data.copy() %}
{%    do data.update({'state_name': '{0}-{1}'.format(target, k)})%}
{%    do data.update({'target': target})%}
{%    set sname = data.get('state_name', data['name']) %}
{% set slsname = 'lxc.vm.install-{0}-ssh-key'.format(
                          target.replace('.', '_')) %}
{% set saltr = cloudSettings.root %}
{{sname}}-lxc-root-keygen:
  cmd.run:
    - name: ssh-keygen -t dsa
    - user: root
    - unless: test -e /root/.ssh/id_dsa
  file.copy:
    - name: {{saltr}}/lxc.pub
    - source: /root/.ssh/id_dsa.pub
    - user: root
    - watch:
      - cmd: {{sname}}-lxc-root-keygen

{{sname}}-lxc.vm-install-ssh-key:
  file.managed:
    - name: {{slspath}}
    - watch:
      - file: {{sname}}-lxc-root-keygen
    - user: root
    - mode: 750
    - makedirs: true
    - contents: |
                inskey:
                  ssh_auth.present:
                    - source: salt://lxc.pub
                    - user: root
  salt.state:
    - tgt: [{{name}}]
    - expr_form: list
    - sls: {{slsname.replace('/', '.')}}
    - concurrent: True
    - watch:
      - file: {{sname}}-lxc-vm-install-ssh-key
    - watch_in:
      - mc_proxy: {{sname}}-lxc-ssh-key
{{sname}}-lxc-root-keygen-clean:
  file.absent:
    - name: {{saltr}}/lxc.pub
    - watch:
      - salt: {{sname}}-lxc-vm-install-ssh-key
{% endfor %}
{% endfor %}
