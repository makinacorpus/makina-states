
firewall-preinstall:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: firewall-postinstall
      - mc_proxy: firewall-preconf
      - mc_proxy: firewall-postconf
      - mc_proxy: firewall-prerestart
firewall-postinstall:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: firewall-preconf
      - mc_proxy: firewall-postconf
      - mc_proxy: firewall-prerestart
firewall-preconf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: firewall-postconf
      - mc_proxy: firewall-prerestart
firewall-postconf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: firewall-prerestart
      - mc_proxy: firewall-postrestart
firewall-prerestart:
  mc_proxy.hook:
    - watch:
      - mc_proxy: shorewall-prerestart
    - watch_in:
      - mc_proxy: firewall-postrestart
firewall-postrestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: firewall-predisable
firewall-predisable:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: firewall-postdisable
firewall-postdisable:
  mc_proxy.hook: []
