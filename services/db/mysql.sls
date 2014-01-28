{# -*- coding: utf-8 -*-
#
# All states are encapsulated in macros.
# So you'll need to run the macros to get something done.
# Check mysql_example.sls file for examples of usage.
#
# MySQL default custom file
# ------------------------configuration (services.db.mysql)
# Set this grain/pillar to override the default makina-states configuration
# file,
# makina-states.services.mysql.cnf
#
# No autoconf
# -------------
# Set this grain/pillar to true to disable mysql automatic configuration:
# makina-states.services.mysql.noautoconf
#
#
# BE CAREFUL: mysql_base() macros should only be called once on a server
# else several states with the same name will be created. There're no
# state_uid prefix on this macro and it's normal, you do not want to install
# several MySQL services on one server.
#}

{# Load defaults values ----------------------------------------- #}

{%- import "makina-states/_macros/services.jinja" as services with context %}
{%- set localsettings = services.localsettings %}
{%- set nodetypes = services.nodetypes %}
{%- set locs = localsettings.locations %}
{%- set mysqlData = services.mysqlSettings %}
{{- services.register('db.mysql') }}

include:
  - {{services.statesPref}}backup.dbsmartbackup

{# MACRO mysql_base()
# - install the mysql packages, and python bindings for mysql
# - install a custom /etc/mysql/conf.d/local.cnf config script
# - reload salt modules to get the mysql salt modules available
# - ensure root password is set on prod servers
# - define the mysql restart/reload states, add watch_in on theses ones
#    * makina-mysql-service (restart)
#    * makina-mysql-service-reload (reload)
#
# Parameters:
# * mycnf_file: If you do not like the current template, add yours
#       the current one is salt://makina-states/files/etc/mysql/conf.d/local.cnf
#}
{%- macro mysql_base(mycnf_file=None) %}
{#-
# Note that python-mysqlDb binding is required for salt module to be loaded
#}
makina-mysql-pkgs:
  pkg.installed:
    - pkgs:
      - {{ mysqlData.packages.main }}
      - {{ mysqlData.packages.python }}
      - {{ mysqlData.packages.dev }}

{#-
# Ensure mysqlDb python binding is available for the minion
# as it's needed to execute later mysql modules
#}
mysql-salt-pythonmysqldb-pip-install:
  pip.installed:
    - name: mysql-python==1.2.4
    - bin_env: /salt-venv/bin/pip
    - require:
      - pkg: makina-mysql-pkgs

mysql-salt-pythonmysqldb-pip-install-module-reloader:
  cmd.watch:
    - name:
            echo "Reloading Modules as mysql python bindings were installed"
    {# WARNING: WE NEED TO REFRESH THE MYSQL MODULE #}
    - reload_modules: true
    - watch:
      - pip: mysql-salt-pythonmysqldb-pip-install

{%- if not mycnf_file %}
{%-   set mycnf_file = "salt://makina-states/files/" + mysqlData.etcdir + "/local.cnf" %}
{%- endif %}
{# ----------- MAGIC MYSQL AUTO TUNING -----------------
Some heavy memory usage settings could be used on mysql settings:
Below are the rules we use to compute some default magic values for tuning settings.
Note that you can enforce any of theses settings by putting some value fro them in
mysqlData (so in the pillar for example).
The most important setting for this tuning is the amount of the total memory you
allow for MySQL, given by the % of total memory set in mysqlData.memory_usage_percent
So starting from total memory * given percentage we use (let's call it available memory):
* innodb_buffer_pool_size: 50% of avail.
* key_buffer_size:
* query_cache_size: 20% of avail. limit to 500M as a starting point
# -- per connections
* max_connections -> impacts on per conn memory settings (which are big) and number of tables and files opened
* innodb_log_buffer_size:
* thread_stack
* thread_cache_size
* sort_buffer_size
# -- others
 * tmp_table_size == max_heap_table_size : If working data memory for a request
              gets bigger than that then file backed temproray tables will be used
              (and it will, by definition, be big ones), the bigger the better
              but you'll need RAM, again.
* table_open_cache
* table_definition_cache

Now let's do the magic:
#}
{# first get the Mo of memory, cpu and disks on the system #}
{%- set full_mem = grains['mem_total'] %}
{%- set nb_cpus = grains['num_cpus'] %}
{# Then extract memory that we could use for this MySQL server #}
{%- set available_mem = full_mem * mysqlData.memory_usage_percent / 100 %}

{# Now for all non set tuning parameters try to fill the gaps #}
{# ---- NUMBER OF CONNECTIONS       #}
{%- if mysqlData.nb_connections %}
{%-  set nb_connections = mysqlData.nb_connections %}
{%- else %}
{%-  set nb_connections = 100 %}
{%- endif %}

{# ---- QUERY CACHE SIZE            #}
{%- set query_cache_size_M = (available_mem / 5)|int %}
{%- if query_cache_size_M > 500 %}
{%-   set query_cache_size_M = 500 %}
{%- endif %}

{# ---- INNODB BUFFER                #}
{# Values cannot be used in default/context as others as we need to compute from previous values #}
{%- if mysqlData.innodb_buffer_pool_size_M %}
{%-   set innodb_buffer_pool_size_M = mysqlData.innodb_buffer_pool_size_M %}
{%- else %}
{%-   set innodb_buffer_pool_size_M = (available_mem / 2)|int %}
{%- endif %}
{# Try to divide this buffer in instances of 1Go #}
{%- if mysqlData.innodb_buffer_pool_instances %}
{%-   set innodb_buffer_pool_instances = mysqlData.innodb_buffer_pool_instances %}
{%- else %}
{%-   set innodb_buffer_pool_instances = (innodb_buffer_pool_size_M / 1024)|round(0)|int %}
{%-   if innodb_buffer_pool_instances < 1 %}
{%-     set innodb_buffer_pool_instances = 1 %}
{%-   endif %}
{%- endif %}
{# Try to set this to 25% of innodb_buffer_pool_size #}
{%- if mysqlData.innodb_log_buffer_size_M %}
{%-   set innodb_log_buffer_size_M = mysqlData.innodb_log_buffer_size_M %}
{%- else %}
{%-   set innodb_log_buffer_size_M = (innodb_buffer_pool_size_M / 4)|round(0)|int %}
{%- endif %}

{# ------- INNODB other settings     #}
{%- set innodb_flush_method = 'fdatasync' %}
{# recommended value is 2*nb cpu + nb of disks, we assume one disk #}
{%- set innodb_thread_concurrency = (nb_cpus + 1) * 2 %}
{# Should we sync binary logs at each commits or prey for no server outage? #}
{%- set sync_binlog = 0 %}
{# innodb_flush_log_at_trx_commit
   1 = Full ACID, but slow, log written at commit + sync disk
   0 = log written every second + sync disk, BUT nothing at commit (kill of mysql can loose last transactions)
   2 = log written every second + sync disk, and log written at commit without sync disk (server outage can loose transactions)
#}
{% set innodb_flush_log_at_trx_commit = 1 %}

{# --------- Settings related to number of tables #}
{# This is by default 8M, should store all tables and indexes informations #}
{%- if mysqlData.number_of_table_indicator < 251 %}
{%-   set innodb_additional_mem_pool_size_M = 8 %}
{%- elif mysqlData.number_of_table_indicator < 501 %}
{%-   set innodb_additional_mem_pool_size_M = 16 %}
{%- elif mysqlData.number_of_table_indicator < 1001 %}
{%-   set innodb_additional_mem_pool_size_M = 24 %}
{%- else %}
{%-   set innodb_additional_mem_pool_size_M = 32 %}
{%- endif %}
{# TABLE CACHE
  table_open_cache should be max joined tables in queries * nb connections
  table_cache is the old name now it's table_open_cache and by default 400
  the system open_file_limit may not be good enough
  If server crash try to tweak "sysctl fs.file-max" or check mysql ulimit
  Warning /etc/security/limits.conf is not read by upstart (it's for users)
  so the increase of file limits must be set in upstart script
  @http://askubuntu.com/questions/288471/mysql-cant-open-files-after-updating-server-errno-24
#}
{%- set table_definition_cache = mysqlData.number_of_table_indicator %}
{%- set table_open_cache = nb_connections * 8 %}
{# this should be table_open_cache * nb_connections #}
{%- set open_file_limit = nb_connections * table_open_cache %}

{# ------------ OTHERS                           #}
{# tmp_table_size: On queries using temporary data, ig this data gets bigger than
 that then the temporary memory things becames real physical temporary tables
 and things gets very slow, but this must be some free RAM when the request is
 running, so if you use something like 1024Mo prey that queries using this amount
 of temporary data are not running too often...
#}
{%- set tmp_table_size_M= (available_mem / 10)|int %}
makina-mysql-settings:
  file.managed:
    - name: {{ mysqlData.etcdir }}/local.cnf
    - source: "{{ mycnf_file }}"
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - show_diff: True
    - defaults:
        var_log: {{ logs.var_log_dir }}
        mode: "production"
        port: {{ mysqlData.port }}
        sockdir: "{{ mysqlData.sockdir }}"
        basedir: "{{ mysqlData.basedir }}"
        datadir: "{{ mysqlData.datadir }}"
        tmpdir: "{{ mysqlData.tmpdir }}"
        sharedir: "{{ mysqlData.sharedir }}"
        noDNS: "{{ mysqlData.noDNS }}"
        isPercona: {{ mysqlData.isPercona }}
        isOracle: {{ mysqlData.isOracle }}
        isMariaDB: {{ mysqlData.isMariaDB }}
        nb_connections : {{ nb_connections }}
        query_cache_size: "{{ query_cache_size_M }}"
        innodb_buffer_pool_size: {{ innodb_buffer_pool_size_M }}
        innodb_buffer_pool_instances: {{ innodb_buffer_pool_instances }}
        innodb_log_buffer_size: {{ innodb_log_buffer_size_M }}
        innodb_flush_method: {{ innodb_flush_method }}
        innodb_thread_concurrency: {{ innodb_thread_concurrency }}
        innodb_flush_log_at_trx_commit: {{ innodb_flush_log_at_trx_commit }}
        innodb_additional_mem_pool_size: {{ innodb_additional_mem_pool_size_M }}
        table_definition_cache: {{ table_definition_cache }}
        table_open_cache: {{ table_open_cache }}
        open_file_limit: {{ open_file_limit }}
        tmp_table_size: {{ tmp_table_size_M }}
        sync_binlog: {{ sync_binlog }}
    - context:
        {%- if ('devhost' in nodetypes.registry.actives) %}
        mode: "dev"
        {%- endif %}
        {%- if mysqlData.query_cache_size_M %}
        query_cache_size: {{ mysqlData.query_cache_size_M }}
        {%- endif %}
        {%- if mysqlData.innodb_flush_method %}
        innodb_flush_method: {{ mysqlData.innodb_flush_method }}
        {%- endif %}
        {%- if mysqlData.innodb_thread_concurrency %}
        innodb_thread_concurrency: {{ mysqlData.innodb_thread_concurrency }}
        {%- endif %}
        {%- if mysqlData.innodb_flush_log_at_trx_commit %}
        innodb_flush_log_at_trx_commit: {{ mysqlData.innodb_flush_log_at_trx_commit }}
        {%- endif %}
        {%- if mysqlData.sync_binlog %}
        sync_binlog: {{ mysqlData.sync_binlog }}
        {%- endif %}
        {%- if mysqlData.innodb_additional_mem_pool_size_M %}
        innodb_additional_mem_pool_size: {{ mysqlData.innodb_additional_mem_pool_size_M }}
        {%- endif %}
        {%- if mysqlData.tmp_table_size_M %}
        tmp_table_size: {{ mysqlData.tmp_table_size_M }}
        {%- endif %}

    - require:
      - pkg: makina-mysql-pkgs
    # full service restart in case of changes
    - watch_in:
       - service: makina-mysql-service

{# --- ROOT ACCESS MANAGMENT --------------- #}
{# Alter root password only if we can connect without #}
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

{%- if not('devhost' in nodetypes.registry.actives) %}
{# On anything that is not a dev server we should emit a big fail for empty
 password root access to the MySQL Server #}
security-check-empty-mysql-root-access-socket:
  cmd.run:
    - name: echo "PROBLEM MYSQL ROOT ACESS without password is allowed (socket mode)" && exit 1
    - onlyif: echo "select 'connected'"|mysql -u root -h localhost
    {# Run after the password alteration #}
    - require:
      - pkg: makina-mysql-pkgs
      - cmd: change-empty-mysql-root-access
    {# tested after each mysql reload or restart #}
    - watch:
      - service: makina-mysql-service-reload
      - service: makina-mysql-service

security-check-empty-mysql-root-access-tcpip:
  cmd.run:
    - name: echo "PROBLEM MYSQL ROOT ACCESS without password is allowed (tcp-ip mode)" && exit 1
    - onlyif: echo "select 'connected'"|mysql -u root -h 127.0.0.1
    {# Run after the password alteration #}
    - require:
      - pkg: makina-mysql-pkgs
      - cmd: change-empty-mysql-root-access
    {# tested after each mysql reload or restart #}
    - watch:
      - service: makina-mysql-service-reload
      - service: makina-mysql-service
{% endif %}

{#--- MAIN SERVICE RESTART/RELOAD watchers -------------- #}
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
    {# most watch requisites are linked here with watch_in #}

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
makina-mysql-db-{{ state_uid }}:
  mysql_database.present:
    - name: "{{ db }}"
    - character_set: "{{ character_set }}"
    - connection_host: "{{ mysql_host }}"
    - connection_user: "{{ mysqlData.conn_user }}"
    - connection_pass: "{{ mysqlData.conn_pass }}"
    - saltenv:
      - LC_ALL: en_US.utf8
{%- if user_creation -%}
{%   for currenthost in host -%}
{%-     set host_simple=currenthost.replace('.', '_').replace(' ','_').replace('%','_') %}
makina-mysql-user-{{ state_uid }}-{{ host_simple }}:
  mysql_user.present:
    - name: "{{ user }}"
    - password: "{{ password }}"
    - allow_passwordless: False
    - host: "{{ currenthost }}"
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
    - connection_host: "{{ mysql_host }}"
    - connection_user: "{{ mysqlData.conn_user }}"
    - connection_pass: "{{ mysqlData.conn_pass }}"
    - saltenv:
      - LC_ALL: en_US.utf8
    - require:
      - mysql_database: makina-mysql-db-{{ state_uid }}
      - mysql_user: makina-mysql-user-{{ state_uid }}-{{ host_simple }}
{%-   endfor %}
{%- endif %}
{% endmacro %}
{%- if not localsettings.myDisableAutoConf %}
{{ mysql_base(localsettings.myCnf) }}
{% endif %}
# vim: set nofoldenable:
