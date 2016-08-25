{% set icinga_webSettings = salt['mc_icinga_web.settings']() %}
include:
  - makina-states.services.monitoring.icinga_web.hooks
{% set pkgssettings = salt['mc_pkgs.settings']() %}
icinga_web-base:
  pkgrepo.managed:
    - humanname: icingaweb ppa
    - name: deb http://ppa.launchpad.net/formorer/icinga/ubuntu {{pkgssettings.udist}} main
    - dist: {{pkgssettings.udist}}
    - file: {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/icingaweb.list
    - keyid: 36862847
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: icinga_web-pre-install
    - watch_in:
      - mc_proxy: icinga_web-post-install

icinga_web-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga_web-pre-install
      - pkgrepo: icinga_web-base
    - watch_in:
      - mc_proxy: icinga_web-post-install
    - pkgs:
      {% for package in icinga_webSettings.package %}
      - {{package}}
      {% endfor %}

{% if icinga_webSettings.modules.pnp4nagios.enabled %}
icinga_web-pnp4nagios-pkgs:
  pkg.latest:
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


