{% set icinga2Settings = salt['mc_icinga2.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.monitoring.icinga2.hooks
  - makina-states.services.monitoring.icinga2.repo

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
      - rrdtool
      - librrds-perl
      - libconfig-inifiles-perl
      - libnet-snmp-perl
      - libsnmp-perl
      - libgetopt-long-descriptive-perl
      - libfindbin-libs-perl
