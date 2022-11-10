{# Icinga-web orchestration hooks #}
pnp4nagios-pre-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: pnp4nagios-post-install
      - mc_proxy: pnp4nagios-pre-conf
      - mc_proxy: pnp4nagios-post-conf
      - mc_proxy: pnp4nagios-pre-restart
      - mc_proxy: pnp4nagios-post-restart
pnp4nagios-post-install:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: pnp4nagios-pre-conf
      - mc_proxy: pnp4nagios-post-conf
      - mc_proxy: pnp4nagios-pre-restart
      - mc_proxy: pnp4nagios-post-restart
pnp4nagios-pre-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: pnp4nagios-post-conf
      - mc_proxy: pnp4nagios-pre-restart
      - mc_proxy: pnp4nagios-post-restart
pnp4nagios-post-conf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: pnp4nagios-pre-restart
      - mc_proxy: pnp4nagios-post-restart

pnp4nagios-pre-restart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: pnp4nagios-post-restart

pnp4nagios-post-restart:
  mc_proxy.hook: []
