{# snmpd orchestration hooks #}
snmpd-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: snmpd-post-install-hook
      - mc_proxy: snmpd-pre-conf-hook
      - mc_proxy: snmpd-post-conf-hook
      - mc_proxy: snmpd-pre-restart-hook
      - mc_proxy: snmpd-post-restart-hook

snmpd-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: snmpd-pre-conf-hook
      - mc_proxy: snmpd-post-conf-hook
      - mc_proxy: snmpd-pre-restart-hook
      - mc_proxy: snmpd-post-restart-hook

snmpd-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: snmpd-post-conf-hook
      - mc_proxy: snmpd-pre-restart-hook
      - mc_proxy: snmpd-post-restart-hook

snmpd-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: snmpd-pre-restart-hook
      - mc_proxy: snmpd-post-restart-hook

snmpd-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: snmpd-post-restart-hook

snmpd-post-restart-hook:
  mc_proxy.hook: []


snmpd-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: snmpd-post-hardrestart-hook

snmpd-post-hardrestart-hook:
  mc_proxy.hook: []

