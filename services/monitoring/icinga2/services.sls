include:
  - makina-states.services.monitoring.icinga2.hooks

icinga2-start:
  service.running:
    - name: icinga2
    - enable: True
    - watch:
      - mc_proxy: icinga2-pre-restart
    - watch_in:
      - mc_proxy: icinga2-post-restart

