{%- set locs = salt['mc_locations.settings']() %}
{% set openssh = salt['mc_ssh.settings']() %}
openssh-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - {{ openssh.pkg_client }}

ssh_config:
  file.managed:
    - name: /etc/ssh/ssh_config
    - source: salt://makina-states/files/etc/ssh/ssh_config
    - mode: 755
    - watch:
      - pkg: openssh-pkgs
    - template: jinja
    - context:
      settings: |
                {{salt['mc_utils.json_dump'](salt['mc_ssh.settings']().client)}}
