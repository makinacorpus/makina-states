{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set icinga2Settings = salt['mc_icinga2.settings']() %}
include:
  - makina-states.services.monitoring.icinga2.hooks

icinga2-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga2-pre-install
    - watch_in:
      - mc_proxy: icinga2-post-install
    - pkgs:
      {% for package in icinga2Settings.package %}
      - {{package}}
      {% endfor %}

{% if icinga2Settings.modules.ido2db.enabled %}
icinga2-ido2db-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga2-pre-install
      - pkg: icinga2-pkgs
    - watch_in:
      - mc_proxy: icinga2-post-install
    - pkgs:
      {% for package in icinga2Settings.modules.ido2db.package %}
      - {{package}}
      {% endfor %}
{% endif %}

{% if icinga2Settings.modules.cgi.enabled %}
icinga2-cgi-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga2-pre-install
      - pkg: icinga2-pkgs
    - watch_in:
      - mc_proxy: icinga2-post-install
    - pkgs:
      {% for package in icinga2Settings.modules.cgi.package %}
      - {{package}}
      {% endfor %}
{% endif %}

{% if icinga2Settings.modules['nagios-plugins'].enabled %}
icinga2-nagios-plugins-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga2-pre-install
      - pkg: icinga2-pkgs
    - watch_in:
      - mc_proxy: icinga2-post-install
    - pkgs:
      {% for package in icinga2Settings.modules['nagios-plugins'].package %}
      - {{package}}
      {% endfor %}
{% endif %}

