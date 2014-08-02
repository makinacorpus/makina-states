{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set uwsgiSettings = salt['mc_uwsgi.settings']() %}
include:
  - makina-states.services.proxy.uwsgi.hooks
uwsgi-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: uwsgi-pre-install
    - watch_in:
      - mc_proxy: uwsgi-post-install
    - pkgs:
      {% for package in uwsgiSettings.package %}
      - {{package}}
      {% endfor %}
