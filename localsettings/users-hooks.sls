users-pre-hook:
  mc_proxy.hook:
    - require_in:
      - mc_proxy: users-ready-hook
users-ready-hook:
  mc_proxy.hook: []
