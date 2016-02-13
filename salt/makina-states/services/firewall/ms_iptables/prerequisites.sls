{% set data = salt['mc_ms_iptables.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.firewall.ms_iptables.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
ms_iptables-pkgs:
  pkg.latest:
  #pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{data.packages}}
    - require_in:
      - mc_proxy: ms_iptables-postinstall
{% endif %}
