include:
  - makina-states.services.monitoring.snmpd.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% set dodl=True %}
{% if grains['os'] in ['Debian'] %}
{% if grains["osrelease"][0] < "6" %}
{% set dodl=False %}
{% endif %}
{% endif %}

snmpd-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - watch:
      - mc_proxy: snmpd-pre-install-hook
    - watch_in:
      - mc_proxy: snmpd-post-install-hook
    - pkgs:
      - snmp
      {% if dodl %}- snmp-mibs-downloader{% endif%}
      - libsensors4
      - libsnmp-base
      {% if grains['os'] in ['Debian'] %}
      - libsnmp15
      {% else %}
      - libsnmp30
      {% endif %}
      - libsnmp-perl
      - nagios-plugins-basic
      - snmpd
      - libsnmp-dev
{% endif %}
