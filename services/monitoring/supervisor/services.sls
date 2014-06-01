include:
  - makina-states.services.monitoring.supervisor.hooks

supervisor-start:
  service.running:
    - name: ms_supervisor
    - enable: True
    - watch:
      - mc_proxy: supervisor-pre-restart
    - watch_in:
      - mc_proxy: supervisor-post-restart

