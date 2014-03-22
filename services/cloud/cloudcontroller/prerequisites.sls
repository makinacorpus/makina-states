{% import "makina-states/_macros/services.jinja" as services with context %}
{% set localsettings = salt['mc_localsettings.settings']() %} %}
include:
  - makina-states.services.cloud.cloudcontroller.hooks

saltcloud-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - sshpass
    - require:
      - mc_proxy: salt-cloud-preinstall
