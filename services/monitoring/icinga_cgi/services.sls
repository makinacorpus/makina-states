include:
  - makina-states.services.monitoring.icinga_cgi.hooks
{#
icinga_cgi-start:
  service.running:
    - name: icinga_cgi
    - enable: True
    - watch:
      - mc_proxy: icinga_cgi-pre-restart
    - watch_in:
      - mc_proxy: icinga_cgi-post-restart

#}
