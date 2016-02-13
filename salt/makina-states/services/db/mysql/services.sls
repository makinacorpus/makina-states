{%- set mysqlData = salt['mc_mysql.settings']() %}
include:
  - makina-states.services.db.mysql.hooks
  - makina-states.services.db.mysql.checkroot

makina-mysql-service:
  service.running:
    - name: {{ mysqlData.service }}
    - watch:
      - mc_proxy: mysql-pre-hardrestart-hook
    - watch_in:
      - mc_proxy: mysql-post-hardrestart-hook

makina-mysql-service-reload:
  service.running:
    - name: {{ mysqlData.service }}
    - enable: True
    - require:
      - mc_proxy: mysql-pre-restart-hook
    - require_in:
      - mc_proxy: mysql-post-restart-hook
  cmd.wait:
    - name: service mysql reload
    {# workaround for Failed to reload mysql.service: Job type reload is not applicable for unit mysql.service.
     systemctl reload mysql wont work
     service mysql reload works
   #}
    - watch:
      - service: makina-mysql-service-reload
      - mc_proxy: mysql-pre-restart-hook
    - watch_in:
      - mc_proxy: mysql-post-restart-hook
