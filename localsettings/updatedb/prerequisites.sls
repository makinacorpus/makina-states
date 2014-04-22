include:
  - makina-states.localsettings.updatedb.hooks

mlocate-pkgs:
  pkg.installed:
    - names:
      - mlocate
    - watch:
      - mc_proxy: updatedb-pre-install
    - watch_in:
      - mc_proxy: updatedb-post-install
