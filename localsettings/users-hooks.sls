groups-pre-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: groups-ready-hook
groups-ready-hook:
  mc_proxy.hook:
   - watch_in:
      - mc_proxy: users-ready-hook
      - mc_proxy: users-pre-hook
users-pre-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: users-ready-hook
users-ready-hook:
  mc_proxy.hook: []
