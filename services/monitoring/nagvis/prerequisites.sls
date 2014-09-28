{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set nagvisSettings = salt['mc_nagvis.settings']() %}
include:
  - makina-states.services.monitoring.nagvis.hooks

nagvis-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: nagvis-pre-install
    - watch_in:
      - mc_proxy: nagvis-post-install
    - pkgs:
      {% for package in nagvisSettings.package %}
      - {{package}}
      {% endfor %}

