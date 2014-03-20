{%- import "makina-states/_macros/services.jinja" as services with context %}
{%- set localsettings = services.localsettings %}
{%- set locs = localsettings.locations %}
{% set openssh = services.sshSettings %}
opensshd-pkgs:
  pkg.{{localsettings.installmode}}:
    - pkgs:
      - {{ openssh.pkg_server }}

sshd_banner:
  file.managed:
    - name: {{ openssh.banner }}
    - source: {{ openssh.banner_src }}
    - template: jinja
    - watch_in:
      - service: openssh-svc

sshd_config:
  file.managed:
    - name: /etc/ssh/sshd_config
    - source: salt://makina-states/files/etc/ssh/sshd_config
    - template: jinja
    - context:
      settings: {{services.sshSettings.server.settings|yaml}}
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
