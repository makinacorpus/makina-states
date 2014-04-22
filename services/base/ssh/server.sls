{%- set locs = salt['mc_locations.settings']() %}
{% set openssh = salt['mc_ssh.settings']() %}
sshgroup:
  group.present:
    - name: {{salt['mc_ssh.settings']().server.group}}


opensshd-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - {{ openssh.pkg_server }}

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
    - name: /etc/ssh/sshd_config
    - source: salt://makina-states/files/etc/ssh/sshd_config
    - template: jinja
    - context:
      settings: |
                {{salt['mc_utils.json_dump'](salt['mc_ssh.settings']().server.settings)}}
    - watch_in:
      - service: openssh-svc

openssh-svc:
  service.running:
    - enable: True
    - watch:
      - file: sshd_config
    {%- if grains['os_family'] == 'Debian' %}
    - name: ssh
    {% else %}
    - name: sshd
    {%- endif %}
