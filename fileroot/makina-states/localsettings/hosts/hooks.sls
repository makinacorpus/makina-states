
makina-hosts-state-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-hosts-hostfiles-pre
makina-hosts-hostfiles-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-hosts-hostfiles-post
makina-hosts-hostfiles-post:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: makina-hosts-state-post
makina-hosts-state-post:
  mc_proxy.hook: []
