include:
  - makina-states.localsettings.pkgs.hooks

ms-before-systemd:
  mc_proxy.hook:
    - require:
      - mc_proxy: after-pkg-install-proxy
    - watch_in:
      - mc_proxy: ms-after-systemd

ms-after-systemd:
  mc_proxy.hook: []

