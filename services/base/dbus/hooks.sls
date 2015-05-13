{# dbus orchestration hooks #}
dbus-preinstall:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dbus-postinstall
      - mc_proxy: dbus-preconf
      - mc_proxy: dbus-postconf
      - mc_proxy: dbus-prerestart
      - mc_proxy: dbus-postrestart

dbus-postinstall:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dbus-preconf
      - mc_proxy: dbus-postconf
      - mc_proxy: dbus-prerestart
      - mc_proxy: dbus-postrestart

dbus-preconf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dbus-postconf
      - mc_proxy: dbus-prerestart
      - mc_proxy: dbus-postrestart

dbus-postconf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dbus-prerestart
      - mc_proxy: dbus-postrestart

dbus-prerestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dbus-postrestart

dbus-postrestart:
  mc_proxy.hook: []


dbus-prehardrestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: dbus-posthardrestart

dbus-posthardrestart:
  mc_proxy.hook: []

