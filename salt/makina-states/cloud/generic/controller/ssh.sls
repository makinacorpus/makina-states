{% set cloudSettings = salt['mc_cloud.settings']() %}
include:
  - makina-states.localsettings.users
  - makina-states.services.base.ssh.rootkey

saltcloud-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - sshpass
