{% set icinga2Settings = salt['mc_icinga2.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}

include:
  - makina-states.services.monitoring.icinga2.hooks

icinga2-base:
  file.absent:
    - name: {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/icinga.list
    - watch:
      - mc_proxy: icinga2-pre-repo
  cmd.run:
    - name: wget http://packages.icinga.org/icinga.key -O - | apt-key add -
    - user: root
    - unless: apt-key list|grep -q Icinga
    - watch:
      - file: icinga2-base
      - mc_proxy: icinga2-pre-repo
  pkgrepo.managed:
    - humanname: icinga ppa
    - name: deb http://ppa.launchpad.net/formorer/icinga/ubuntu {{pkgssettings.ppa_dist}} main
    - dist: {{pkgssettings.ppa_dist}}
    - file: {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/icinga2.list
    - keyid: "36862847"
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: icinga2-pre-repo
      - cmd: icinga2-base
      - file: icinga2-base
    - watch_in:
      - mc_proxy: icinga2-post-repo
