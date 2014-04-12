include:
  - makina-states.services.firewall.shorewall.hooks
shorewall-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - shorewall6
      - shorewall
    - require_in:
      - mc_proxy: shorewall-postinstall

