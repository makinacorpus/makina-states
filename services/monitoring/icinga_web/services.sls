include:
  - makina-states.services.monitoring.icinga_web.hooks
{#
icinga_web-start:
  service.running:
    - name: icinga_web
    - enable: True
    - watch:
      - mc_proxy: icinga_web-pre-restart
    - watch_in:
      - mc_proxy: icinga_web-post-restart

#}
