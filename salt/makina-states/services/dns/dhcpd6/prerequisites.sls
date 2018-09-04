{% set settings = salt['mc_dhcpd6.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.dns.dhcpd6.hooks
dhcpd6-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{settings.pkgs}}
    - watch:
      - mc_proxy: dhcpd6-pre-install
    - watch_in:
      - mc_proxy: dhcpd6-post-install
