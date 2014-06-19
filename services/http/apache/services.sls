{% set apacheSettings = salt['mc_apache.settings']() %}
{% set apacheConfCheck = apacheSettings.apacheConfCheck %}
include:
  - makina-states.services.http.apache.hooks

{# Configuration checker, always run before restart of graceful restart #}
makina-apache-conf-syntax-check:
  cmd.script:
    - source: {{ apacheSettings.apacheConfCheck }}
    - stateful: True
    - watch:
      - mc_proxy: makina-apache-post-conf
    - watch_in:
      - mc_proxy: makina-apache-pre-restart
      - mc_proxy: makina-apache-pre-reload

{# MAIN SERVICE RESTART/RELOAD watchers #}
makina-apache-restart:
  service.running:
    - name: {{ apacheSettings.service }}
    - enable: True
    # most watch requisites are linked here with watch_in
    - watch_in:
      - mc_proxy: makina-apache-post-restart
      # restart service in case of package install
    - watch:
      - mc_proxy: makina-apache-post-inst
      - mc_proxy: makina-apache-pre-restart

{# For VirtualHosts change graceful reloads should be enough #}
makina-apache-reload:
  service.running:
    - name: {{ apacheSettings.service }}
    - watch_in:
      - mc_proxy: makina-apache-post-reload
    - watch:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-post-conf
      - mc_proxy: makina-apache-pre-reload
    - enable: True
    - reload: True
