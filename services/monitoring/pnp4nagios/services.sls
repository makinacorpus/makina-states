include:
  - makina-states.services.monitoring.pnp4nagios.hooks

pnp4nagios-npcd-start:
  service.running:
    - name: npcd
    - enable: True
    - watch:
      - mc_proxy: pnp4nagios-pre-restart
    - watch_in:
      - mc_proxy: pnp4nagios-post-restart

