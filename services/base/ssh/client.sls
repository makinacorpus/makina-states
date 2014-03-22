{%- import "makina-states/_macros/services.jinja" as services with context %}
{%- set localsettings = services.localsettings %}
{%- set locs = salt['mc_localsettings']()['locations'] %}
{% set openssh = salt['mc_ssh.settings']() %}
openssh-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - {{ openssh.pkg_client }}

ssh_config:
  file.managed:
    - name: /etc/ssh/ssh_config
    - source: salt://makina-states/files/etc/ssh/ssh_config
    - watch:
      - pkg: openssh-pkgs
    - template: jinja
    - context:
      settings: {{salt['mc_ssh.settings']().client|yaml}}
