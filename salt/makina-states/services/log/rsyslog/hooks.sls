{# rsyslog orchestration hooks #}
rsyslog-pre-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rsyslog-post-install-hook
      - mc_proxy: rsyslog-pre-conf-hook
      - mc_proxy: rsyslog-post-conf-hook
      - mc_proxy: rsyslog-pre-restart-hook
      - mc_proxy: rsyslog-post-restart-hook

rsyslog-post-install-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rsyslog-pre-conf-hook
      - mc_proxy: rsyslog-post-conf-hook
      - mc_proxy: rsyslog-pre-restart-hook
      - mc_proxy: rsyslog-post-restart-hook

rsyslog-pre-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rsyslog-post-conf-hook
      - mc_proxy: rsyslog-pre-restart-hook
      - mc_proxy: rsyslog-post-restart-hook

rsyslog-post-conf-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rsyslog-pre-restart-hook
      - mc_proxy: rsyslog-post-restart-hook

rsyslog-pre-restart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rsyslog-post-restart-hook

rsyslog-post-restart-hook:
  mc_proxy.hook: []


rsyslog-pre-hardrestart-hook:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: rsyslog-post-hardrestart-hook

rsyslog-post-hardrestart-hook:
  mc_proxy.hook: []

