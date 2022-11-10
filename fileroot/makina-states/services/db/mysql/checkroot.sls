{# --- ROOT ACCESS MANAGMENT --------------- #}

{# Alter root password only if we can connect without #}
include:
  - makina-states.services.db.mysql.hooks

{%- set mysqlSettings = salt['mc_mysql.settings']() %}
{% if mysqlSettings.mysql57onward %}
change-empty-mysql-root-access-socket:
  cmd.run:
    - name: |
        mysql -u root \
          -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{{ mysqlSettings.root_passwd }}'; FLUSH PRIVILEGES;"
    - onlyif: echo "select 'connected'" | mysql -u root
    # tested after each mysql reload or restart
    - watch_in:
      - mc_proxy: mysql-setup-access
    - watch:
      - mc_proxy: mysql-setup-access-pre
      - mc_proxy: mysql-post-restart-hook
      - mc_proxy: mysql-post-hardrestart-hook
change-empty-mysql-root-access-tcp-via-create:
  cmd.run:
    - name: |
        mysql -u root --password='{{ mysqlSettings.root_passwd }}' \
          -e "CREATE USER IF NOT EXISTS 'root'@'127.0.0.1' IDENTIFIED WITH mysql_native_password BY '{{ mysqlSettings.root_passwd }}'; FLUSH PRIVILEGES;"
    - onlyif: |
              echo "select 'connected'" | mysql -u root --host=127.0.0.1
              if [ "x${?}" = "x0" ];then exit 0;fi
              echo "select 'connected'" | mysql -u root --host=127.0.0.1 --password='{{ mysqlSettings.root_passwd }}'
              if [ "x${?}" = "x1" ];then exit 0;fi
              exit 1
    # tested after each mysql reload or restart
    - watch_in:
      - mc_proxy: mysql-setup-access
    - watch:
      - cmd: change-empty-mysql-root-access-socket
      - mc_proxy: mysql-setup-access-pre
      - mc_proxy: mysql-post-restart-hook
      - mc_proxy: mysql-post-hardrestart-hook
change-empty-mysql-root-access-tcp:
  cmd.run:
    - name: |
        mysql -u root --password='{{ mysqlSettings.root_passwd }}' \
          -e "ALTER USER 'root'@'127.0.0.1' IDENTIFIED WITH mysql_native_password BY '{{ mysqlSettings.root_passwd }}'; FLUSH PRIVILEGES;"
    - onlyif: |
              echo "select 'connected'" | mysql -u root --host=127.0.0.1
              if [ "x${?}" = "x0" ];then exit 0;fi
              echo "select 'connected'" | mysql -u root --host=127.0.0.1 --password='{{ mysqlSettings.root_passwd }}'
              if [ "x${?}" = "x1" ];then exit 0;fi
              exit 1
    # tested after each mysql reload or restart
    - watch_in:
      - mc_proxy: mysql-setup-access
    - watch:
      - cmd: change-empty-mysql-root-access-socket
      - cmd: change-empty-mysql-root-access-tcp-via-create
      - mc_proxy: mysql-setup-access-pre
      - mc_proxy: mysql-post-restart-hook
      - mc_proxy: mysql-post-hardrestart-hook

change-empty-mysql-root-grant-access-tcp:
  cmd.run:
    - name: |
        mysql -u root --password='{{ mysqlSettings.root_passwd }}' \
          -e "GRANT ALL PRIVILEGES ON *.* TO 'root'@'127.0.0.1' WITH GRANT OPTION; FLUSH PRIVILEGES;"
    - unless: |
              echo "select 'connected'" | mysql -u root -p --host=127.0.0.1 --password='{{ mysqlSettings.root_passwd }}'  mysql
    # tested after each mysql reload or restart
    - watch_in:
      - mc_proxy: mysql-setup-access
    - watch:
      - cmd: change-empty-mysql-root-access-socket
      - cmd: change-empty-mysql-root-access-tcp-via-create
      - mc_proxy: mysql-setup-access-pre
      - mc_proxy: mysql-post-restart-hook
      - mc_proxy: mysql-post-hardrestart-hook
{% else %}
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
{% endif %}

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
