{%- set icingaSettings = salt['mc_icinga.settings']() %}
{%- set venv = icingaSettings['location'] + "/venv" %}
include:
  - makina-states.services.monitoring.icinga.hooks

icinga-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - watch:
      - mc_proxy: icinga-pre-install-hook
    - watch_in:
      - mc_proxy: icinga-post-install-hook
    - pkgs:
      - icinga-common
      - icinga-core
      - icinga-doc
