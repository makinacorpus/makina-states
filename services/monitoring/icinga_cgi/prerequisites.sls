{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set icinga_cgiSettings = salt['mc_icinga_cgi.settings']() %}
include:
  - makina-states.services.monitoring.icinga_cgi.hooks

icinga_cgi-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga_cgi-pre-install
    - watch_in:
      - mc_proxy: icinga_cgi-post-install
    - pkgs:
      {% for package in icinga_cgiSettings.package %}
      - {{package}}
      {% endfor %}

