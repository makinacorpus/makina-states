{%- set mysqlData = salt['mc_mysql.settings']() %}
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
{%- macro mysql_db(db,
                  user = None,
                  host=None,
                  password=None,
                  character_set=None,
                  collate=None,
                  user_creation=True,
                  mysql_host=None,
                  state_uid=None) -%}
{#--- MYSQL directories, users, database, grants -------------- #}
{%- if not state_uid %}
{%-   set state_uid=db.replace('.', '_').replace(' ','_') %}
{%- endif %}
{%- if not host %}
{%-   set host=['%'] %}
{%- elif host is string %}
{%-   set host=[host] %}
{%- endif %}
{%- if not character_set %}
{%-   set character_set=mysqlData.character_set %}
{%- endif %}
{%- if not mysql_host %}
{%-   set mysql_host=mysqlData.conn_host %}
{%- endif %}
{%- if not collate %}
{%-   set collate=mysqlData.collate %}
{%- endif %}
{%- if user_creation -%}
{#- user name is by default the db name #}
{%-   if not user -%}
{%-     set user = db %}
{%-   endif -%}
{%-   if not password -%}
{%-     set password = '' %}
{%-   endif -%}
{%- endif -%}
{#Important, do not remove this space, needed if the macro is call with "-" #}

makina-mysql-db-{{ state_uid }}:
  mysql_database.present:
    - name: "{{ db }}"
    - character_set: "{{ character_set }}"
    - connection_host: "{{ mysql_host }}"
    - connection_user: "{{ mysqlData.conn_user }}"
    - connection_pass: "{{ mysqlData.conn_pass }}"
    - saltenv:
      - LC_ALL: en_US.utf8
    - require_in:
      - mc_proxy: mysql-db-create-hook
{%- if user_creation -%}
{{- mysql_user(user, password, mysql_host=mysql_host, 
               host=host, state_uid=state_uid, databases=[db]) }}
{%- endif %}
{%- endmacro %}

{% macro mysql_user(
    user, password, host=None, grant='ALL',
    allow_passwordless=False, mysql_host=None, databases=None, state_uid=None) %}
{%- if not host %}
{%-   set host=['%'] %}
{%- elif host is string %}
{%-   set host=[host] %}
{%- endif %}
{%- if not databases %}
{%-   set databases = [] %}
{%- endif %}
{%- if not mysql_host %}
{%-   set mysql_host=mysqlData.conn_host %}
{%- endif %}
{%- if not state_uid %}
{%-   set state_uid=(user+''.join(host)).replace(
            '%', '_').replace('.', '_').replace(' ','_') %}
{%- endif %}
{%- for currenthost in host %}
{%-  set host_simple=currenthost.replace('.', '_').replace(' ','_').replace('%','_') %}
makina-mysql-cuser-{{ state_uid }}-{{ host_simple }}:
  mysql_user.present:
    - name: "{{ user }}"
    - password: "{{ password }}"
    - allow_passwordless: {{allow_passwordless}}
    - host: "{{ currenthost }}"
    - connection_host: "{{ mysql_host }}"
    - connection_user: "{{ mysqlData.conn_user }}"
    - connection_pass: "{{ mysqlData.conn_pass }}"
    - saltenv:
      - LC_ALL: en_US.utf8
    - require:
      - mc_proxy: mysql-db-create-hook
    - require_in:
      - mc_proxy: mysql-db-create-user-hook

{%-  if not databases %}
{#- global user as superuser #}
{%-   set databases = ['*', '*.*'] %}
{%-  endif %}
{%-  for db in databases %}
{%-   set sdb = db.replace('*', 'star') %}
makina-mysql-cuser-grants-{{ state_uid }}-{{ host_simple }}-{{sdb}}:
  mysql_grants.present:
    - name: "MySQL General grants for {{ user }}"
    - grant: "{{grant}}"
    - database: "{{ db }}.*"
    - user: "{{ user }}"
    - host: "{{ currenthost }}"
    - connection_host: "{{ mysql_host }}"
    - connection_user: "{{ mysqlData.conn_user }}"
    - connection_pass: "{{ mysqlData.conn_pass }}"
    - saltenv:
      - LC_ALL: en_US.utf8
    - require:
      - mc_proxy: mysql-db-create-user-hook
    - require_in:
      - mc_proxy: mysql-db-grant-hook
{%-  endfor %}
{%- endfor %}
{% endmacro %}
