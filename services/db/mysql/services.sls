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
    - reload: True
    - watch:
      - mc_proxy: mysql-pre-restart-hook
    - watch_in:
      - mc_proxy: mysql-post-restart-hook
