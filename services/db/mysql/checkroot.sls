{# --- ROOT ACCESS MANAGMENT --------------- #}
{# Alter root password only if we can connect without #}
include:
  - makina-states.services.db.mysql.hooks

{%- set mysqlSettings = salt['mc_mysql.settings']() %}
change-empty-mysql-root-access-socket:
  cmd.run:
    - name: mysqladmin -u root flush-privileges password "{{ mysqlSettings.root_passwd }}"
    - onlyif: echo "select 'connected'"|mysql -u root
    # tested after each mysql reload or restart
    - watch_in:
      - mc_proxy: mysql-setup-access
    - watch:
      - mc_proxy: mysql-setup-access-pre
      - mc_proxy: mysql-post-restart-hook
      - mc_proxy: mysql-post-hardrestart-hook

change-empty-mysql-root-access-tcp:
  cmd.run:
    - name: mysqladmin -u root -h 127.0.0.1 flush-privileges password "{{ mysqlSettings.root_passwd }}"
    - onlyif: echo "select 'connected'"|mysql -u root -h 127.0.0.1
    # tested after each mysql reload or restart
    - watch_in:
      - mc_proxy: mysql-setup-access
    - watch:
      - mc_proxy: mysql-setup-access-pre
      - mc_proxy: mysql-post-restart-hook
      - mc_proxy: mysql-post-hardrestart-hook

security-check-empty-mysql-root-access-socket:
  cmd.run:
    - name: echo "PROBLEM MYSQL ROOT ACESS without password is allowed (socket mode)" && exit 1
    - onlyif: echo "select 'connected'"|mysql -u root -h localhost
    {# tested after each mysql reload or restart #}
    - watch_in:
      - mc_proxy: mysql-setup-access
    - watch:
      - mc_proxy: mysql-setup-access-pre
      - cmd: change-empty-mysql-root-access-socket

security-check-empty-mysql-root-access-tcpip:
  cmd.run:
    - name: echo "PROBLEM MYSQL ROOT ACCESS without password is allowed (tcp-ip mode)" && exit 1
    - onlyif: echo "select 'connected'"|mysql -u root -h 127.0.0.1
    {# tested after each mysql reload or restart #}
    - watch_in:
      - mc_proxy: mysql-setup-access
    - watch:
      - mc_proxy: mysql-setup-access-pre
      - cmd: change-empty-mysql-root-access-tcp
