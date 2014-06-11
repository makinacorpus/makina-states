{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set icinga_webSettings = salt['mc_icinga_web.settings']() %}
include:
  - makina-states.services.monitoring.icinga_web.hooks

icinga_web-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga_web-pre-install
    - watch_in:
      - mc_proxy: icinga_web-post-install
    - pkgs:
      {% for package in icinga_webSettings.package %}
      - {{package}}
      {% endfor %}

# TODO: add dependencies: nginx and php
# ubuntu package of icinga_web depends on apache2.
