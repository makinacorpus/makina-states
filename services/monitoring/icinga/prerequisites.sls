{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set icingaSettings = salt['mc_icinga.settings']() %}
include:
  - makina-states.services.monitoring.icinga.hooks

icinga-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga-pre-install
    - watch_in:
      - mc_proxy: icinga-post-install
    - pkgs:
      {% for package in icingaSettings.package %}
      - {{package}}
      {% endfor %}

{% if icingaSettings.modules.ido2db.enabled %}
icinga-ido2db-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga-pre-install
      - pkg: icinga-pkgs
    - watch_in:
      - mc_proxy: icinga-post-install
    - pkgs:
      {% for package in icingaSettings.modules.ido2db.package %}
      - {{package}}
      {% endfor %}
{% endif %}

{% if icingaSettings.modules.cgi.enabled %}
icinga-cgi-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga-pre-install
      - pkg: icinga-pkgs
    - watch_in:
      - mc_proxy: icinga-post-install
    - pkgs:
      {% for package in icingaSettings.modules.cgi.package %}
      - {{package}}
      {% endfor %}
{% endif %}

{% if icingaSettings.modules['nagios-plugins'].enabled %}
icinga-nagios-plugins-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - mc_proxy: icinga-pre-install
      - pkg: icinga-pkgs
    - watch_in:
      - mc_proxy: icinga-post-install
    - pkgs:
      {% for package in icingaSettings.modules['nagios-plugins'].package %}
      - {{package}}
      {% endfor %}
{% endif %}
