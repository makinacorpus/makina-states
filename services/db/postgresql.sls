#
# This states file aims to configure postgresql server
#
#  You have
#   - postgresql_db: a macro to define databases with a default group as owner:
#   - postgresql_user: a macro to define an user, his privileges and groups
#
#--- STATES EXAMPLES --------------------------------
#
# You can use them in your own states as follow: {#
#
#    {% import "makina-states/services/db/postgresql.sls" as pgsql with context %}
#    {{ pgsql.postgresql_base() }}
#    {% set db_name = dbdata['db_name'] %}
#    {% set db_tablespace = dbdata['db_tablespace'] %}
#    {% set db_user = dbdata['db_user'] %}
#    {% set db_password = dbdata['db_password'] %}
#    {{ pgsql.postgresql_db(db_name, tablespace=db_tablespace) }}
#    {{ pgsql.postgresql_user(db_user,
#                             db_password,
#                             groups=['{0}_owners'.format(db_name)]) }}
#    {% endfor %} 
#
#    #}
#
# Remember that states should not contain any secret password or user.
# So here for example dbdata would be coming from a default macro
# loading pillar data.
#
#--- PILLAR EXAMPLE -------------------------------------
#
# You can define via pillar the default user to run psql command as:
#
#    makina.postgresql.user: foo (default: postgres)
#
# You can also define in pillar databases and users respecting naming convention:
# By default the owner of the database is a group with the same name suffixed
# with _owner for the user to be added to. We assign then users to this group
#
# Define a database and its owner as follow (see salt.states.postgres_database.present)
# bar-makina-postgresql:
#   name: foo (opt, default; 'bar')
#   encoding: foo (opt, default; utf8)
#   template: foo (opt, default; template0)
#   tablespace: foo (opt, default; pg_default)
# This will create a 'bar' database owned by the group 'bar_owners'
#
# Define a user a follow (see salt.states.postgres_user.present)
# bar-makina-postgresql-user:
#   password: h4x
#   groups: bar-owners (opt, default: [])
#   encrypted: True (opt, default: True)
#   superuser: True (opt, default: False)
#   createdb: True (opt, default: False)
#   replication: True (opt, default: False)
# will create a bar user with 'h4x' password and in group 'bar-owners' (the one of the precedent database)
#
# eg:
#    mydb-makina-postgresql: {}
#    mydb-makina-postgresql-user:
#      password: ckan-password
#      superuser: True
#      groups:
#        - mydb_owners
#
#
#
#
#
{% set default_psql_user = salt['config.get']('makina.postgresql.user', 'postgres') %}

{% macro postgresql_base() %}
postgresql-pkgs:
  pkg.installed:
    - pkgs:
      - postgresql
      - libpq-dev
      - python-virtualenv

#--- MAIN SERVICE RESTART/RELOAD watchers --------------

makina-postgresql-service:
  service.running:
    - name: postgresql
    - require:
      - pkg: postgresql-pkgs
    - watch:
      - pkg: postgresql-pkgs

makina-postgresql-service-reload:
  service.running:
    - name: postgresql
    - require:
      - pkg: postgresql-pkgs
    - enable: True
    - reload: True
    # most watch requisites are linked here with watch_in

{% endmacro %}

{% macro postgresql_db(db,
                       owner=None,
                       tablespace='pg_default',
                       template='template0',
                       encoding='utf8',
                       psql_user=default_psql_user
) -%}
#--- POSTGRESQL CLUSTER directories, users, database, grants --------------
{# owner name is by default the db name #}
{% if not owner -%}
{%   set owner = '%s_owners' % db %}
{% endif -%}
{{owner}}-makina-postresql-group:
   postgres_group.present:
    - name: {{owner}}
    - runas: {{psql_user}}
    - require:
      - service: makina-postgresql-service

{{owner}}-makina-postgresql-group-login:
  cmd.run:
    - name: echo "ALTER ROLE {{owner}} WITH LOGIN;"|psql
    - user: {{psql_user}}
    - require:
      - postgres_group: {{owner}}-makina-postresql-group

{{db}}-makina-postgresql-database:
  cmd.run:
    - name: createdb {{db}} -E {{encoding}} -O {{owner}} -T {{template }} -D {{tablespace}}
    - unless: test "$(psql -l|awk '{print $1}'|grep -w {{db}}|wc -l)" != "0"
    - user: {{psql_user}}
    - require:
      - service: makina-postgresql-service
      - postgres_group: {{owner}}-makina-postresql-group

{{db}}-owners-makina-postresql-grant:
  cmd.run:
    - name: echo "GRANT ALL PRIVILEGES ON DATABASE {{db}} TO {{owner}};"|psql
    - user: {{psql_user}}
    - require:
      - postgres_group: {{owner}}-makina-postresql-group
      - cmd: {{db}}-makina-postgresql-database
{% endmacro %}

{% macro postgresql_user(user,
                         password,
                         groups=None,
                         createdb=False,
                         superuser=False,
                         replication=False,
                         encrypted=True,
                         psql_user=default_psql_user
) -%}
{% if not groups %}
{%   set groups = [] %}
{% endif %}
{{user}}-makina-postgresql-user:
  postgres_user.present:
    - name: {{ user }}
    - password: {{password}}
    - runas: {{psql_user}}
    {% if createdb %}- createdb: True {% endif %}
    {% if superuser %}- superuser: True {% endif %}
    {% if replication %}- replication: True {% endif %}
    {% if encrypted %}- encrypted: True {% endif %}
    {% if groups %}- groups: {{','.join(groups)}}{% endif %}
    - require:
      - service: makina-postgresql-service
      {% for g in  groups %}- cmd: {{g}}-makina-postgresql-group-login
      {% endfor %}
{% endmacro %}

{{ postgresql_base() }}
{% for dbk, data in pillar.items() %}
{%   if dbk.endswith('-makina-postgresql') %}
{%     set db = data.get('name', dbk.split('-makina-postgresql')[0]) %}
{%     set encoding=data.get('encoding', 'utf8') %}
{%     set owner=data.get('owner', None) %}
{%     set template=data.get('encoding', 'template0')%}
{%     set tablespace=data.get('tablesplace', 'pg_default')%}
{{     postgresql_db(db=db,
                     owner=owner,
                     tablesplace=tablesplace,
                     encoding=encoding,
                     template=template) }}
{%     endif %}
{% endfor %}
{% for userk, data in pillar.items() %}
{%   if userk.endswith('-makina-postgresql-user') %}
{%     set user = data.get('name', userk.split('-makina-postgresql-user')[0]) %}
{%     set groups = data.get('groups', []) %}
{%     set pw = data['password'] %}
{%     set superuser = data.get('superuser', False) %}
{%     set encrypted = data.get('encrypted', True) %}
{%     set replication = data.get('replication', False) %}
{%     set createdb = data.get('createdb', False) %}
{{     postgresql_user(user=user,
                       password=pw,
                       createdb=createdb,
                       groups=groups,
                       encrypted=encrypted,
                       superuser=superuser,
                       replication=replication) }}
{%   endif %}
{% endfor %}
