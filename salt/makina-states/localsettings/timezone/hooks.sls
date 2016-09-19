include:
  - makina-states.localsettings.locales.hooks

timezone-pre-inst:
  mc_proxy.hook:
    - watch:
      - mc_proxy: locales-post-conf
    - watch_in:
      - mc_proxy: timezone-post-inst

timezone-post-inst:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: timezone-pre-conf

timezone-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: timezone-post-conf

timezone-post-conf:
  mc_proxy.hook: []
