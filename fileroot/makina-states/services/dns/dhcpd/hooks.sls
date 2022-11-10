dhcpd-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd-post-install
      - mc_proxy: dhcpd-pre-conf
      - mc_proxy: dhcpd-post-conf
      - mc_proxy: dhcpd-pre-reload
dhcpd-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd-pre-conf
      - mc_proxy: dhcpd-post-conf
      - mc_proxy: dhcpd-pre-reload

dhcpd-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd-post-conf
      - mc_proxy: dhcpd-pre-reload
      - mc_proxy: dhcpd-check-conf
dhcpd-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd-pre-reload
      - mc_proxy: dhcpd-check-conf
dhcpd-check-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd-pre-reload
      - mc_proxy: dhcpd-pre-restart
dhcpd-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd-post-restart
dhcpd-post-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd-post-end
dhcpd-pre-reload:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd-post-reload
dhcpd-post-reload:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dhcpd-post-end
dhcpd-post-end:
  mc_proxy.hook: []
