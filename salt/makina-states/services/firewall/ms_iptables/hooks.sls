include:
  - makina-states.localsettings.network.hooks
# retrocompat, wire into shorewall hooks
  - makina-states.services.firewall.shorewall.hooks
  - makina-states.services.firewall.firewalld.hooks
ms_iptables-preinstall:
  mc_proxy.hook:
    - require:
      - mc_proxy: shorewall-postdisable
      - mc_proxy: network-last-hook
      - mc_proxy: dbus-postrestart
      - mc_proxy: dbus-posthardrestart
    - watch_in:
      - mc_proxy: ms_iptables-postinstall
      - mc_proxy: ms_iptables-preconf
      - mc_proxy: ms_iptables-postconf
      - mc_proxy: ms_iptables-prerestart
ms_iptables-postinstall:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ms_iptables-preconf
      - mc_proxy: ms_iptables-postconf
      - mc_proxy: ms_iptables-prerestart
ms_iptables-preconf:
  mc_proxy.hook:
    - require:
      - mc_proxy: shorewall-postconf
    - watch_in:
      - mc_proxy: ms_iptables-postconf
      - mc_proxy: ms_iptables-prerestart
    - require_in:
      - mc_proxy: shorewall-prerestart
ms_iptables-postconf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ms_iptables-prerestart
      - mc_proxy: ms_iptables-postrestart
ms_iptables-prerestart:
  mc_proxy.hook:
    - require:
      - mc_proxy: shorewall-prerestart
    - watch_in:
      - mc_proxy: ms_iptables-postrestart
ms_iptables-postrestart:
  mc_proxy.hook:
    - require:
      - mc_proxy: shorewall-postrestart
