ms-apparmor-pre:
  mc_proxy.hook: []

ms-apparmor-cfg-pre:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ms-apparmor-pre
    - watch_in:
      - mc_proxy: ms-apparmor-cfg-post

ms-apparmor-cfg-post:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ms-apparmor-cfg-pre
    - watch_in:
      - mc_proxy: ms-apparmor-post

ms-apparmor-post:
  mc_proxy.hook: []
