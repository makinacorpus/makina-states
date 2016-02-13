nodejs-pre-prefix-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nodejs-post-prefix-install

nodejs-post-prefix-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nodejs-post-install

nodejs-pre-system-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nodejs-post-system-install

nodejs-post-system-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: nodejs-post-install

nodejs-post-install:
  mc_proxy.hook: []
