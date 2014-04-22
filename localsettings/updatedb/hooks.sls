
updatedb-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: updatedb-post-install

updatedb-post-install:
  mc_proxy.hook: []

