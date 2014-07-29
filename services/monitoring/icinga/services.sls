include:
  - makina-states.services.monitoring.icinga.hooks

icinga-start:
  service.running:
    - name: icinga
    - enable: True
    - watch:
      - mc_proxy: icinga-pre-restart
    - watch_in:
      - mc_proxy: icinga-post-restart

