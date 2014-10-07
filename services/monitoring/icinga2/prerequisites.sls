{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set icinga2Settings = salt['mc_icinga2.settings']() %}
include:
  - makina-states.services.monitoring.icinga2.hooks

{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% if grains['os_family'] in ['Debian'] %}
{% set dist = pkgssettings.udist %}
{% endif %}
{% if grains['os'] in ['Debian'] %}
{% set dist = pkgssettings.ubuntu_lts %}
{% endif %}

icinga2-base:
  cmd.run:
    - name: wget http://packages.icinga.org/icinga.key -O - | apt-key add -
    - user: root
    - unless: apt-key list|grep -q Icinga
  pkgrepo.managed:
    - humanname: icinga ppa
    - name: deb  http://packages.icinga.org/{{grains['os'].lower()}}/ icinga-{{dist}} main
    - dist: icinga-{{dist}}
    - file: {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/icinga.list
    - watch:
      - mc_proxy: icinga2-pre-install
      - cmd: icinga2-base

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
