{# hooks for etckeeper orchestration #}
include:
  - makina-states.localsettings.pkgs.hooks
  - makina-states.localsettings.git.hooks
etckeeper-inst-pre:
  mc_proxy.hook:
    - watch:
      - mc_proxy: after-pkg-install-proxy
      - mc_proxy: install-recent-git-post
    - watch_in:
      - mc_proxy: etckeeper-inst-post
etckeeper-inst-post:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: etckeeper-conf-pre

etckeeper-conf-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: etckeeper-conf-post

etckeeper-conf-post:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: etckeeper-run-pre
etckeeper-run-pre:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: etckeeper-run-hook
etckeeper-run-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: etckeeper-post-run-hook
etckeeper-post-run-hook:
  mc_proxy.hook: []

