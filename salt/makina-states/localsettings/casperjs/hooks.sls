casperjs-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: casperjs-post-install

casperjs-post-install:
  mc_proxy.hook: []
