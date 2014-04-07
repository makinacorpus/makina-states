bind-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: bind-post-install
      - mc_proxy: bind-pre-conf
      - mc_proxy: bind-post-conf
      - mc_proxy: bind-pre-reload
bind-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: bind-pre-conf
      - mc_proxy: bind-post-conf
      - mc_proxy: bind-pre-reload

bind-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: bind-post-conf
      - mc_proxy: bind-pre-reload
      - mc_proxy: bind-check-conf
bind-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: bind-pre-reload
      - mc_proxy: bind-check-conf
bind-check-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: bind-pre-reload
      - mc_proxy: bind-pre-restart
bind-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: bind-post-restart
bind-post-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: bind-post-end
bind-pre-reload:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: bind-post-reload
bind-post-reload:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: bind-post-end
bind-post-end:
  mc_proxy.hook: []
