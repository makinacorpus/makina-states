include:
  - makina-states.services.monitoring.circus.hooks

circus-start:
  service.running:
    - name: circusd
    - enable: True
    - watch:
      - mc_proxy: circus-pre-restart
    - watch_in:
      - mc_proxy: circus-post-restart

