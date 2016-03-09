{% set settings = salt['mc_dhcpd.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.dns.dhcpd.hooks
dhcpd-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{settings.pkgs}}
    - watch:
      - mc_proxy: dhcpd-pre-install
    - watch_in:
      - mc_proxy: dhcpd-post-install
