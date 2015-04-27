include:
  - makina-states.localsettings.desktoptools.hooks

ms-desktoptools-cfg:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ms-desktoptools-pkg-post
    - watch_in:
      - mc_proxy: ms-desktoptools-post
