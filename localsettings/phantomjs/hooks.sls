phantomjs-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: phantomjs-post-install

phantomjs-post-install:
  mc_proxy.hook: []
