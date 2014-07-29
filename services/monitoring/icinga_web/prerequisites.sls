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

{% if icinga_webSettings.modules.pnp4nagios.enabled %}
icinga_web-pnp4nagios-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga_web-pre-install
      - pkg: icinga_web-pkgs
    - watch_in:
      - mc_proxy: icinga_web-post-install
    - pkgs:
      {% for package in icinga_webSettings.modules.pnp4nagios.package %}
      - {{package}}
      {% endfor %}
{% endif %}


