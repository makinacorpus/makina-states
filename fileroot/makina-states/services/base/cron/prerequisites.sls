{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_cron.settings']() %}
include:
  - makina-states.services.base.cron.hooks
cron-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{settings.packages}}
    - watch:
      - mc_proxy: cron-preinstall
    - watch_in:
      - mc_proxy: cron-postinstall
