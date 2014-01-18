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
#    makina-states.services.postgresql.user: foo (default: postgres)
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
# bar-makina-services-postgresql-user:
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
#    mydb-makina-services-postgresql-user:
#      password: ckan-password
#      superuser: True
#      groups:
#        - mydb_owners

{% import "makina-states/_macros/services.jinja" as services with context %}
{% set services = services %}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set locs = localsettings.locations %}
{{ services.register('db.postgresql') }}
{% set default_user = services.postgresqlUser %}

#
# Hooks to attach to for orchestration purpose
# - We create in order:
#   - groups
#   - databases
#   - extensions
#   - users
#

{% set orchestrate = {} %}
{% for ver in services.pgVers %}
{% set preext = ver+'-makina-postgresql-pre-create-ext' %}
{% set postext = ver+'-makina-postgresql-post-create-ext' %}
{% set pregroup = ver+'-makina-postgresql-pre-create-group' %}
{% set postgroup = ver+'-makina-postgresql-post-create-group' %}
{% set predb = ver+'-makina-postgresql-pre-create-db' %}
{% set postdb = ver+'-makina-postgresql-post-create-db' %}
{% set preuser = ver+'-makina-postgresql-pre-create-user' %}
{% set postuser = ver+'-makina-postgresql-post-create-user' %}

{% do orchestrate.update({ver: {} }) %}
{% do orchestrate[ver].update({
  'pregroup': pregroup,
  'postgroup': postgroup,
  'predb': predb,
  'postdb': postdb,
  'preuser': preuser,
  'postuser': postuser,
  'preext': preext,
  'postext': postext,
}) %}
{{services.funcs.dummy(pregroup, '''
    - require:
      - service: makina-postgresql-service
''')}}
{{services.funcs.dummy(postgroup)}}

{{services.funcs.dummy(predb, '''
    - require:
      - cmd: {0}
      - service: makina-postgresql-service
'''.format(postgroup))}}
{{services.funcs.dummy(postdb)}}

{{services.funcs.dummy(preuser, '''
    - require:
      - cmd: {0}
      - service: makina-postgresql-service
'''.format(postdb))}}
{{services.funcs.dummy(postuser)}}

{{services.funcs.dummy(preext, '''
    - require:
      - pkg: postgresql-pkgs
      - cmd: {0}
      - service: makina-postgresql-service
'''.format(postdb))}}
{{services.funcs.dummy(postext)}}
{% endfor %}

{% macro install_pg_exts(exts,
                         db=None,
                         dbs=None,
                         version=None,
                         versions=None,
                         user=default_user) %}
{% if not dbs %}
{% set dbs = ['template1'] %}
{% endif %}
{% if db %}
{% do dbs.append(db) %}
{% endif %}
{% if not versions %}
{% set versions = [services.defaultPgVersion] %}
{% endif %}
{% if version %}
{% do versions.append(version) %}
{% endif %}

{% for version in versions %}
{% for ext in exts %}
{% for db in dbs %}
{{version}}-{{db}}-{{ext}}-makina-postgresql:
  cmd.run:
    - require_in:
      - cmd: {{ orchestrate[version]['postext'] }}
    - require:
      - cmd: {{ orchestrate[version]['preext'] }}
    - user: {{ user }}
    - name: echo "CREATE EXTENSION {{ext}};"|psql {{db}}
    - unless: test "$(echo "\dx"|psql -q -P tuples_only=on,footer=off,border=0 {{db}}|awk '{print $1}'|grep {{ext}}|wc -l)" != "0"
{% endfor%}
{% endfor%}
{% endfor%}
{% endmacro %}

{% macro install_pg_ext(ext, db=None,  dbs=None, version=None, versions=None, user=default_user) %}
{{ install_pg_exts([ext], db=None, dbs=dbs) }}
{% endmacro %}

{% macro postgresql_base() %}
{% if grains['os_family'] in ['Debian'] %}
pgsql-repo:
  pkgrepo.managed:
    - name: deb http://apt.postgresql.org/pub/repos/apt/ {{localsettings.dist}}-pgdg main
    - file: {{ locs.conf_dir }}/apt/sources.list.d/pgsql.list
    - keyid: 'ACCC4CF8'
    - keyserver: {{localsettings.keyserver }}

{% endif %}

postgresql-pkgs:
  pkg.installed:
    - pkgs:
      - python-virtualenv {# noop #}
      {% if grains['os_family'] in ['Debian'] %}
      {% for pgver in services.pgVers %}
      - postgresql-{{pgver}}
      - postgresql-server-dev-{{pgver}}
      {% endfor %}
      - libpq-dev
      - postgresql-contrib
      {% endif %}
    {% if grains['os_family'] in ['Debian'] %}
    - require:
      - pkgrepo: pgsql-repo
    {% endif %}

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

#
#--- POSTGRESQL CLUSTER directories, users, database, grants --------------
#
{% macro postgresql_group(group,
                          user=default_user,
                          version=services.defaultPgVersion) %}
{{ version }}-{{ group }}-makina-postresql-group:
   postgres_group.present:
    - name: {{ group }}
    - runas: {{ user }}
    - require:
      - cmd: {{orchestrate[version]['pregroup']}}

{{ version }}-{{ group }}-makina-postgresql-group-login:
  cmd.run:
    - name: echo "ALTER ROLE {{ group }} WITH LOGIN;"|psql
    - user: {{ user }}
    - require:
      - postgres_group: {{ version }}-{{ group }}-makina-postresql-group
    - require_in:
      - cmd: {{orchestrate[version]['postgroup']}}
{% endmacro %}

#
# Create a database, and an owner group which owns it
#
{% macro postgresql_db(db,
                       owner=None,
                       tablespace='pg_default',
                       template='template1',
                       encoding='utf8',
                       user=default_user,
                       version=services.defaultPgVersion
) -%}
{# group name is by default the db name #}
{% if not owner -%}
{%   set owner = '%s_groups' % db %}
{% endif -%}

{{ postgresql_group(owner, user=user) }}

{{version}}-{{ db }}-makina-postgresql-database:
  cmd.run:
    - name: createdb {{ db }} -E {{ encoding }} -O {{ owner }} -T {{template }} -D {{ tablespace }}
    - unless: test "$(psql -l|awk '{print $1}'|grep -w {{ db }}|wc -l)" != "0"
    - user: {{ user }}
    - require:
      - cmd: {{orchestrate[version]['predb']}}

{{ version }}-{{ owner }}-groups-makina-postresql-grant:
  cmd.run:
    - name: echo "GRANT ALL PRIVILEGES ON DATABASE {{ db }} TO {{ owner }};"|psql
    - user: {{ user }}
    - require:
      - cmd: {{version}}-{{ db }}-makina-postgresql-database
    - require_in:
      - cmd: {{orchestrate[version]['postdb'] }}

{{ install_pg_ext('adminpack', db=db, version=version, user=default_user) }}
{% endmacro %}

#
# Create and grant privs to a postgresql user
#
{% macro postgresql_user(name,
                         password,
                         groups=None,
                         createdb=False,
                         superuser=False,
                         replication=False,
                         encrypted=True,
                         user=default_user,
                         version=services.defaultPgVersion
) -%}
{% if not groups %}
{%   set groups = [] %}
{% endif %}
{{version}}-{{ name }}-makina-services-postgresql-user:
  postgres_user.present:
    - name: {{ name }}
    - password: {{ password }}
    - runas: {{ user }}
    {% if createdb %}- createdb: True {% endif %}
    {% if superuser %}- superuser: True {% endif %}
    {% if replication %}- replication: True {% endif %}
    {% if encrypted %}- encrypted: True {% endif %}
    {% if groups %}- groups: {{ ','.join(groups) }}{% endif %}
    - require_in:
      - cmd: {{orchestrate[version]['postuser']}}
    - require:
      - cmd: {{orchestrate[version]['preuser']}}
{% endmacro %}

{{ postgresql_base() }}

{% for version in services.pgVers %}
pgwrapper-{{version}}-makina-postgresql:
  file.managed:
    - name: /usr/bin/pg-wrapper-{{version}}.sh
    - source: salt://makina-states/files/usr/bin/pg-wrapper.sh
    - template: jinja
    - mode: 755
    - require_in:
      - cmd: {{orchestrate[version]['predb']}}
      - cmd: {{orchestrate[version]['pregroup']}}
      - cmd: {{orchestrate[version]['preuser']}}
      - cmd: {{orchestrate[version]['preext']}}
    - context:
      version: {{version}}

{%  for binary in [
 'vacuumdb', 'dropdb', 'clusterdb', 'reindexdb', 'pg_dump', 'pg_basebackup',
 'pg_receivexlog', 'psql', 'createdb', 'dropuser', 'pg_dumpall', 'createuser',
 'pg_restore', 'pg_isready', 'createlang', 'droplang'
] %}
pgwrapper-{{binary}}-{{version}}-makina-postgresql:
  file.managed:
    - name: /usr/bin/{{binary}}-{{version}}
    - source: salt://makina-states/files/usr/bin/pgbin-wrapper.sh
    - template: jinja
    - mode: 755
    - require_in:
      - cmd: {{orchestrate[version]['predb']}}
      - cmd: {{orchestrate[version]['pregroup']}}
      - cmd: {{orchestrate[version]['preuser']}}
      - cmd: {{orchestrate[version]['preext']}}
    - require:
      - file: pgwrapper-{{version}}-makina-postgresql
    - context:
      version: {{ version }}
      binary: {{ binary }}
{%  endfor %}
{% endfor %}

{% for version in services.pgVers %}
{% for db, data in services.pgDbs %}
{%     set encoding=data.get('encoding', 'utf8') %}
{%     set owner=data.get('owner', None) %}
{%     set template=data.get('encoding', 'template0')%}
{%     set tablespace=data.get('tablesplace', 'pg_default')%}
{{     postgresql_db(db=db,
                     owner=owner,
                     tablesplace=tablesplace,
                     encoding=encoding,
                     version=version,
                     template=template) }}
{% endfor %}
{% for user, data in services.postgresqlUsers %}
{%     set groups = data.get('groups', []) %}
{%     set pw = data['password'] %}
{%     set superuser = data.get('superuser', False) %}
{%     set encrypted = data.get('encrypted', True) %}
{%     set replication = data.get('replication', False) %}
{%     set createdb = data.get('createdb', False) %}
{{     postgresql_user(user=default_user,
                       password=pw,
                       createdb=createdb,
                       groups=groups,
                       version=version,
                       encrypted=encrypted,
                       superuser=superuser,
                       replication=replication) }}

{% endfor %}
{% endfor %}
# vim:set nofoldenable:
