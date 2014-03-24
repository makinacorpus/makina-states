{% set localsettings = salt['mc_localsettings.settings']() %}
include:
  - makina-states.cloud.generic.hooks

saltcloud-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - sshpass
    - require_in:
      - mc_proxy: cloud-generic-pre-pre-deploy
