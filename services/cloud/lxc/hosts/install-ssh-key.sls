{% import "makina-states/_macros/controllers.jinja" as controllers with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
include:
  - makina-states.services.cloud.lxc.hooks
{% set cloudSettings= services.cloudSettings %}
{% set lxcSettings = services.lxcSettings %}
{% for target, containers in services.lxcSettings.containers.items() %}
{# authorize root from cloudcontroller to connect via ssh on targets #}
{% set slsname = 'lxc-hosts/install-{0}-ssh-key'.format(
            target.replace('.', '_')) %}
{% if controllers.registry.is.mastersalt %}
{% set saltr = saltmac.msaltRoot %}
{%else %}
{% set saltr = saltmac.saltRoot %}
{%endif %}
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
