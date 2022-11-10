makina-hostname-state-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-hostname-hostname-pre
makina-hostname-hostname-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-hostname-hostname-post
makina-hostname-hostname-post:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-hostname-state-post
makina-hostname-state-post:
  mc_proxy.hook: []
