cloud-generic-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-final

cloud-generic-final:
  mc_proxy.hook: []
