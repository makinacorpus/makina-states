locales-post-inst:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: locales-pre-conf

locales-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: locales-post-conf

locales-post-conf:
  mc_proxy.hook: []
