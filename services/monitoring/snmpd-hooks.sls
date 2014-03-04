{# SNMPD orchestration hooks #}
snmpd-pre-restart:
  mc_proxy.hook:
      - watch_in:
        - mc_proxy: snmpd-post-restart
snmpd-post-restart:
  mc_proxy.hook: []
