{# cron orchestration hooks #}
cron-preinstall:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cron-postinstall
      - mc_proxy: cron-preconf
      - mc_proxy: cron-postconf
      - mc_proxy: cron-prerestart
      - mc_proxy: cron-postrestart

cron-postinstall:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cron-preconf
      - mc_proxy: cron-postconf
      - mc_proxy: cron-prerestart
      - mc_proxy: cron-postrestart

cron-preconf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cron-postconf
      - mc_proxy: cron-prerestart
      - mc_proxy: cron-postrestart

cron-postconf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cron-prerestart
      - mc_proxy: cron-postrestart

cron-prerestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cron-postrestart

cron-postrestart:
  mc_proxy.hook: []


cron-prehardrestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: cron-posthardrestart

cron-posthardrestart:
  mc_proxy.hook: []

