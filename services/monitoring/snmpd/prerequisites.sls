include:
  - makina-states.services.monitoring.snmpd.hooks

snmpd-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - watch:
      - mc_proxy: snmpd-pre-install-hook
    - watch_in:
      - mc_proxy: snmpd-post-install-hook
    - pkgs:
      - snmp
      - snmp-mibs-downloader
      - libsensors4
      - libsnmp-base
      - libsnmp30
      - libsnmp-perl
      - nagios-plugins-basic
      - snmpd
