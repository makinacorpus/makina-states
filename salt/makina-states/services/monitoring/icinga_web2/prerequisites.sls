{% set icinga_web2Settings = salt['mc_icinga_web2.settings']() %}
include:
  - makina-states.services.monitoring.icinga_web2.hooks
  - makina-states.services.monitoring.icinga2.repo
{% set pkgssettings = salt['mc_pkgs.settings']() %}
icinga_web2-base:
  mc_proxy.hook:
    - watch:
      - mc_proxy: icinga2-post-repo
      - mc_proxy: icinga_web2-pre-install
    - watch_in:
      - mc_proxy: icinga_web2-post-install

icinga_web2-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga_web2-pre-install
      - mc_proxy: icinga_web2-base
    - watch_in:
      - mc_proxy: icinga_web2-post-install
    - pkgs:
      {% for package in icinga_web2Settings.package %}
      - {{package}}
      {% endfor %}
