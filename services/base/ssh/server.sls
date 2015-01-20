{%- set locs = salt['mc_locations.settings']() %}
include:
  - makina-states.services.base.ssh.hooks

{% if salt['mc_controllers.mastersalt_mode']() %}
{% set openssh = salt['mc_ssh.settings']() %}
opensshd-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - {{ openssh.pkg_server }}
{% if salt['mc_controllers.mastersalt_mode']() %}
sshgroup:
  group.present:
    - name: {{salt['mc_ssh.settings']().server.group}}

{% if openssh.get('banner', '') %}
sshd_banner:
  file.managed:
    - name: {{ openssh.banner }}
    - source: {{ openssh.banner_src }}
    - template: jinja
    - watch_in:
      - service: openssh-svc
{% endif %}

sshd_config:
  file.managed:
    - watch_in:
      - service: openssh-svc
    - name: /etc/ssh/sshd_config
    - source: salt://makina-states/files/etc/ssh/sshd_config
    - template: jinja
    - watch_in:
      - service: openssh-svc
{% endif %}

openssh-svc:
  service.running:
    - enable: True
    {%- if grains['os_family'] == 'Debian' %}
    - name: ssh
    {% else %}
    - name: sshd
    {%- endif %}
{%- endif %}
