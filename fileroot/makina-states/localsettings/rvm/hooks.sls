rvm-install-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rvm-install-post
rvm-install-post:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rvm-setup-pre
rvm-setup-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rvm-setup-post
rvm-setup-post:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rvm-setup-act-pre
rvm-setup-act-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rvm-setup-act-post
rvm-setup-act-post:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rvm-last
rvm-last:
  mc_proxy.hook: []

