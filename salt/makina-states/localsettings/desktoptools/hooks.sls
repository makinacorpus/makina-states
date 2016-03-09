include:
  - makina-states.localsettings.pkgs.hooks

ms-desktoptools-pre:
  mc_proxy.hook:
    - watch:
      - mc_proxy: after-pkg-install-proxy
    - watch_in:
      - mc_proxy: ms-desktoptools-post

ms-desktoptools-pkgm-pre:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ms-desktoptools-pre
    - watch_in:
      - mc_proxy: ms-desktoptools-pkgm-post

ms-desktoptools-pkgm-post:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ms-desktoptools-pkgm-pre
    - watch_in:
      - mc_proxy: ms-desktoptools-pkg-pre

ms-desktoptools-pkg-pre:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ms-desktoptools-pkgm-post
    - watch_in:
      - mc_proxy: ms-desktoptools-pkg-post

ms-desktoptools-pkg-post:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ms-desktoptools-pkg-pre
    - watch_in:
      - mc_proxy: ms-desktoptools-post

ms-desktoptools-post:
  mc_proxy.hook: []
