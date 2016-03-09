{% set icinga2Settings = salt['mc_icinga2.settings']() %}
include:
  - makina-states.services.monitoring.icinga2.hooks

{% set pkgssettings = salt['mc_pkgs.settings']() %}
icinga2-base:
  file.absent:
    - name: {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/icinga.list
  cmd.run:
    - name: wget http://packages.icinga.org/icinga.key -O - | apt-key add -
    - user: root
    - unless: apt-key list|grep -q Icinga
  pkgrepo.managed:
    - humanname: icinga ppa
    - name: deb http://ppa.launchpad.net/formorer/icinga/ubuntu {{pkgssettings.ppa_dist}} main
    - dist: {{pkgssettings.ppa_dist}}
    - file: {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/icinga2.list
    - keyid: "36862847"
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: icinga2-pre-install
      - cmd: icinga2-base
      - file: icinga2-base

icinga2-pkgs:
  pkg.{{pkgssettings['installmode']}}:
    - watch:
      - pkgrepo: icinga2-base
      - mc_proxy: icinga2-pre-install
    - watch_in:
      - mc_proxy: icinga2-post-install
    - pkgs:
      {% for package in icinga2Settings.package %}
      - {{package}}
      {% endfor %}
      {%  for package in icinga2Settings.modules.ido2db.package %}
      - {{package}}
      {%  endfor %}
      - rrdtool
      - librrds-perl
      - libconfig-inifiles-perl
      - libnet-snmp-perl
      - libsnmp-perl
      - libgetopt-long-descriptive-perl
      - libfindbin-libs-perl
