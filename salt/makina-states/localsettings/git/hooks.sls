
install-recent-git-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: install-recent-git-post
install-recent-git-post:
  mc_proxy.hook: []

