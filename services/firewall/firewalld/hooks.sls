include:
  - makina-states.localsettings.network.hooks
# retrocompat, wire into shorewall hooks
  - makina-states.services.firewall.shorewall.hooks
firewalld-preinstall:
  mc_proxy.hook:
    - watch:
      - mc_proxy: shorewall-preinstall
      - mc_proxy: network-last-hook
    - watch_in:
      - mc_proxy: firewalld-postinstall
      - mc_proxy: firewalld-preconf
      - mc_proxy: firewalld-postconf
      - mc_proxy: firewalld-prerestart
      - mc_proxy: firewalld-activation
      - mc_proxy: shorewall-postinstall
      - mc_proxy: shorewall-preconf
      - mc_proxy: shorewall-postconf
      - mc_proxy: shorewall-prerestart
      - mc_proxy: shorewall-activation 
firewalld-postinstall:
  mc_proxy.hook:
    - watch:
      - mc_proxy: shorewall-postinstall
    - watch_in:
      - mc_proxy: firewalld-preconf
      - mc_proxy: firewalld-postconf
      - mc_proxy: firewalld-activation
      - mc_proxy: firewalld-prerestart
      - mc_proxy: shorewall-preconf
      - mc_proxy: shorewall-postconf
      - mc_proxy: shorewall-activation
      - mc_proxy: shorewall-prerestart
firewalld-preconf:
  mc_proxy.hook:
    - watch:
      - mc_proxy: shorewall-preconf 
    - watch_in:
      - mc_proxy: firewalld-postconf
      - mc_proxy: firewalld-prerestart
      - mc_proxy: firewalld-activation
      - mc_proxy: shorewall-postconf
      - mc_proxy: shorewall-prerestart
      - mc_proxy: shorewall-activation
firewalld-postconf:
  mc_proxy.hook:
    - watch:
      - mc_proxy: shorewall-postconf 
    - watch_in:
      - mc_proxy: firewalld-activation
      - mc_proxy: firewalld-prerestart
      - mc_proxy: shorewall-activation
      - mc_proxy: shorewall-prerestart
firewalld-activation:
  mc_proxy.hook:
    - watch:
      - mc_proxy: shorewall-activation 
    - watch_in:
      - mc_proxy: firewalld-prerestart
      - mc_proxy: firewalld-postrestart
      - mc_proxy: shorewall-prerestart
      - mc_proxy: shorewall-postrestart
firewalld-prerestart:
  mc_proxy.hook:
    - watch:
      - mc_proxy: shorewall-prerestart 
    - watch_in:
      - mc_proxy: firewalld-postrestart
firewalld-postrestart:
  mc_proxy.hook:
    - watch:
      - mc_proxy: shorewall-postrestart 
