# -*- coding: utf-8 -*-
#
# Including this state will make nothig, all states are encapsulated in macros.
# So you'll need to run the macros to get something done.
# Check mysql_example.sls file for examples of usage.
#
# BE CAREFUL: mysql_base() macros should only be called once on a server
# else several states with the same name will be created. There're no
# state_uid prefix on this macro and it's normal, you do not want to install
# several MySQL services on one server.

# Load defaults values -----------------------------------------

{% from 'makina-states/services/db/mysql_defaults.jinja' import mysqlData with context %}

{# MACRO mysql_base()
# - install the mysql packages, and python bindings for mysql
# - reload salt modules to get the mysql salt modules available
# - ensure root password is set on prod servers
# - define the mysql restart/reload states, add watch_in on theses ones
#    * makina-mysql-service (restart)
#    * makina-mysql-service-reload (reload)
#}
{% macro mysql_base() %}

#
# Note that python-mysqlDb binding is required for salt module to be loaded
makina-mysql-pkgs:
  pkg.installed:
    - names:
      - {{ mysqlData.packages.main }}
      - {{ mysqlData.packages.python }}
      - {{ mysqlData.packages.dev }}

## Ensure mysqlDb python binding is available for the minion
## as it's needed to execute later mysql modules
mysql-salt-pythonmysqldb-pip-install:
  pip.installed:
    - name: mysql-python==1.2.4
    - bin_env: /salt-venv/bin/pip
    - require:
      - pkg: makina-mysql-pkgs

mysql-salt-pythonmysqldb-pip-install-module-reloader:
  cmd.wait:
    - name: |
            echo "Reloading Modules as mysql python bindings were installed"
    # WARNING: WE NEED TO REFRESH THE MYSQL MODULE
    - reload_modules: true
    - watch:
      - pip: mysql-salt-pythonmysqldb-pip-install


# Alter root password only if we can connect without
change-empty-mysql-root-access:
  cmd.run:
    - name: mysqladmin -u root flush-privileges password "{{ mysqlData.root_passwd }}"
    - onlyif: echo "select 'connected'"|mysql -u root
    - require:
      - pkg: makina-mysql-pkgs
    # tested after each mysql reload or restart
    - watch:
      - service: makina-mysql-service-reload
      - service: makina-mysql-service

{% if not(grains['makina.devhost']) %}
{# On anything that is not a dev server we should emit a big fail for empty
 password root access to the MySQL Server #}
security-check-empty-mysql-root-access-socket:
  cmd.run:
    - name: echo "PROBLEM MYSQL ROOT ACESS without password is allowed (socket mode)" && exit 1
    - onlyif: echo "select 'connected'"|mysql -u root -h localhost
    # Run after the password alteration
    - require:
      - pkg: makina-mysql-pkgs
      - cmd: change-empty-mysql-root-access
    # tested after each mysql reload or restart
    - watch:
      - service: makina-mysql-service-reload
      - service: makina-mysql-service

security-check-empty-mysql-root-access-tcpip:
  cmd.run:
    - name: echo "PROBLEM MYSQL ROOT ACCESS without password is allowed (tcp-ip mode)" && exit 1
    - onlyif: echo "select 'connected'"|mysql -u root -h 127.0.0.1
    # Run after the password alteration
    - require:
      - pkg: makina-mysql-pkgs
      - cmd: change-empty-mysql-root-access
    # tested after each mysql reload or restart
    - watch:
      - service: makina-mysql-service-reload
      - service: makina-mysql-service
{% endif %}

#--- MAIN SERVICE RESTART/RELOAD watchers --------------

makina-mysql-service:
  service.running:
    - name: {{ mysqlData.service }}
    - require:
      - pkg: makina-mysql-pkgs
    - watch:
      - pkg: makina-mysql-pkgs

makina-mysql-service-reload:
  service.running:
    - name: {{ mysqlData.service }}
    - require:
      - pkg: makina-mysql-pkgs
    - enable: True
    - reload: True
    # most watch requisites are linked here with watch_in

{# End of mysql_base() macro #}
{% endmacro %}



{# MACRO mysql_db()
# Do not forget to use mysql_base() macro before using it
# - Create a MySQL database on a MySQL Server (utf8 by default)
# - Create a user with the same name as database and all privileges
# - Optionaly manage this user from a given list of IP
#   * by default the host argument will be '%' (means all)
#   * you can set it to a string value ('localhost')
#   * you can give a list of IP ['10.0.0.1','10.0.0.2',127.0.0.1']
# If you need more than one user and finer grants, set to True the
# bool user_creation and make your own states (@see mysql_example.sls)
#
# The mysql_server argument is the mysql connection host, by default
# we'll use the mysqlData.conn_host value ('localhost' usually)
#}
{% macro mysql_db(db,
                  user = None,
                  host=None,
                  password=None,
                  character_set=None,
                  collate=None,
                  user_creation=True,
                  mysql_host=None,
                  state_uid=None) -%}
#--- MYSQL directories, users, database, grants --------------
{% if not state_uid %}
{%   set state_uid=db.replace('.', '_').replace(' ','_') %}
{% endif %}
{% if not host %}
{%   set host=['%'] %}
{% elif host is string %}
{%   set host=[host] %}
{% endif %}
{% if not character_set %}
{%   set character_set=mysqlData.character_set %}
{% endif %}
{% if not mysql_host %}
{%   set mysql_host=mysqlData.conn_host %}
{% endif %}
{% if not collate %}
{%   set collate=mysqlData.collate %}
{% endif %}
{% if user_creation -%}
{# user name is by default the db name #}
{%   if not user -%}
{%     set user = db %}
{%   endif -%}
{%   if not password -%}
{%     set password = '' %}
{%   endif -%}
{% endif -%}
makina-mysql-db-{{ state_uid }}:
  mysql_database.present:
    - name: "{{ db }}"
    - character_set: "{{ character_set }}"
    - collate: "{{ collate }}"
    - connection_charset: "{{ character_set }}"
    - connection_host: "{{ mysql_host }}"
    - connection_user: "{{ mysqlData.conn_user }}"
    - connection_pass: "{{ mysqlData.conn_pass }}"
    - saltenv:
      - LC_ALL: en_US.utf8
{% if user_creation -%}
{%   for currenthost in host %}
{%     set host_simple=currenthost.replace('.', '_').replace(' ','_').replace('%','_') %}
makina-mysql-user-{{ state_uid }}-{{ host_simple }}:
  mysql_user.present:
    - name: "{{ user }}"
    - password: "{{ password }}"
    - allow_passwordless: False
    - host: "{{ currenthost }}"
    - connection_charset: "{{ character_set }}"
    - connection_host: "{{ mysql_host }}"
    - connection_user: "{{ mysqlData.conn_user }}"
    - connection_pass: "{{ mysqlData.conn_pass }}"
    - saltenv:
      - LC_ALL: en_US.utf8
    - require:
      - mysql_database: makina-mysql-db-{{ state_uid }}
makina-mysql-user-grants-{{ state_uid }}-{{ host_simple }}:
  mysql_grants.present:
    - name: "MySQL General grants for {{ user }}"
    - grant: "ALL"
    - database: "{{ db }}.*"
    - user: "{{ user }}"
    - host: "{{ currenthost }}"
    - connection_charset: "{{ character_set }}"
    - connection_host: "{{ mysql_host }}"
    - connection_user: "{{ mysqlData.conn_user }}"
    - connection_pass: "{{ mysqlData.conn_pass }}"
    - saltenv:
      - LC_ALL: en_US.utf8
    - require:
      - mysql_database: makina-mysql-db-{{ state_uid }}
      - mysql_user: makina-mysql-user-{{ state_uid }}-{{ host_simple }}
{%   endfor %}
{% endif -%}
{% endmacro %}
