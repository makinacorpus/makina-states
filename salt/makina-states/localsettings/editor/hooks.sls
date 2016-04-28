editor-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: editor-post-install

editor-post-install:
  mc_proxy.hook: []
