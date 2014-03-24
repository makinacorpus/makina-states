{% set localsettings = salt['mc_localsettings.settings']() %}
include:
  - makina-states.cloud.generic.hooks.controller

saltcloud-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - sshpass
    - watch_in:
      - mc_proxy: cloud-generic-controller-pre-pre-deploy
