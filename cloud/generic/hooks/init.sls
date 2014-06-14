include:
  - makina-states.localsettings.users.hooks

cloud-generic-pre:
  mc_proxy.hook:
    - watch:
      - mc_proxy: users-ready-hook
    - watch_in:
      - mc_proxy: cloud-generic-final

cloud-sslcerts-pre:
  mc_proxy.hook:
    - watch:
      - mc_proxy: cloud-generic-pre
    - watch_in:
      - mc_proxy: cloud-sslcerts

cloud-sslcerts:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cloud-generic-final

cloud-generic-final:
  mc_proxy.hook: []

