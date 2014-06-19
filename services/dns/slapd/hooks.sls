slapd-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: slapd-post-install
      - mc_proxy: slapd-pre-conf
      - mc_proxy: slapd-post-conf
      - mc_proxy: slapd-pre-reload
slapd-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: slapd-pre-conf
      - mc_proxy: slapd-post-conf
      - mc_proxy: slapd-pre-reload

slapd-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: slapd-post-conf
      - mc_proxy: slapd-pre-reload
      - mc_proxy: slapd-check-conf
slapd-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: slapd-pre-reload
      - mc_proxy: slapd-check-conf
slapd-check-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: slapd-pre-reload
      - mc_proxy: slapd-pre-restart
slapd-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: slapd-post-restart
slapd-post-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: slapd-post-end
slapd-pre-reload:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: slapd-post-reload
slapd-post-reload:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: slapd-post-end
slapd-post-end:
  mc_proxy.hook: []
