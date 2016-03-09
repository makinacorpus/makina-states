{% set data = salt['mc_ms_iptables.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.firewall.ms_iptables.hooks
ms_iptables-pkgs:
  pkg.latest:
  #pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{data.packages}}
    - require_in:
      - mc_proxy: ms_iptables-postinstall
