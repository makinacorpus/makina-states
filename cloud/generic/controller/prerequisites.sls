{% set localsettings = salt['mc_localsettings.settings']() %}
include:
  - makina-states.cloud.generic.hooks.common
  - makina-states.cloud.generic.hooks.controller

saltcloud-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - sshpass
    - watch:
      - mc_proxy: cloud-generic-pre
    - watch_in:
      - mc_proxy: cloud-generic-controller-pre-pre-deploy
