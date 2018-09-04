dhcpd6-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd6-post-install
      - mc_proxy: dhcpd6-pre-conf
      - mc_proxy: dhcpd6-post-conf
      - mc_proxy: dhcpd6-pre-reload
dhcpd6-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd6-pre-conf
      - mc_proxy: dhcpd6-post-conf
      - mc_proxy: dhcpd6-pre-reload

dhcpd6-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd6-post-conf
      - mc_proxy: dhcpd6-pre-reload
      - mc_proxy: dhcpd6-check-conf
dhcpd6-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd6-pre-reload
      - mc_proxy: dhcpd6-check-conf
dhcpd6-check-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd6-pre-reload
      - mc_proxy: dhcpd6-pre-restart
dhcpd6-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd6-post-restart
dhcpd6-post-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd6-post-end
dhcpd6-pre-reload:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd6-post-reload
dhcpd6-post-reload:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd6-post-end
dhcpd6-post-end:
  mc_proxy.hook: []
