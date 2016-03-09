include:
  - makina-states.services.base.ntp.hooks
ntp-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - ntp
      - ntpdate
      - libopts25
    - watch_in:
      - mc_proxy: ntp-post-install-hook
    - watch:
      - mc_proxy: ntp-pre-install-hook
