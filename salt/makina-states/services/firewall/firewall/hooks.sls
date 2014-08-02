# warning: orchestration is done specifically for one
# firewall, those hooks are only for ./*.sls
firewall-preconf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: firewall-postconf
firewall-postconf:
  mc_proxy.hook: []
