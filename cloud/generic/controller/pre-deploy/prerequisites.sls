{% set localsettings = salt['mc_localsettings.settings']() %}
include:
  - makina-states.services.cloud.controller.hooks

saltcloud-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - sshpass
    - require:
      - mc_proxy: salt-cloud-preinstall
