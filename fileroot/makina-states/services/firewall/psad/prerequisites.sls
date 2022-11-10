include:
  - makina-states.services.firewall.psad.hooks

psad-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - psad
    - watch:
      - mc_proxy: psad-pre-install-hook
    - watch_in:
      - mc_proxy: psad-post-install-hook
