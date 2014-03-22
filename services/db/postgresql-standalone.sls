{#-
# see doc/ref/formulaes/services/db/postgresql.rst
#}
{%- import "makina-states/_macros/services.jinja" as services with context %}
{%- import "makina-states/services/db/postgresql-hooks.sls" as dummies with context %}
{%- set orchestrate = dummies.orchestrate %}
{%- set services = services %}
{%- set localsettings = services.localsettings %}
{%- set nodetypes = services.nodetypes %}
{%- set locs = salt['mc_localsettings.settings']()['locations'] %}
{{ salt['mc_macros.register']('services', 'db.postgresql') }}
{%- set default_user = services.postgresqlUser %}

{% macro install_pg_exts(exts,
                         db=None,
                         db_host=None,
                         db_port=None,
                         wait_for_database_creation=None,
                         dbs=None,
                         version=None,
                         versions=None,
                         user=default_user,
                         watch=None,
                         watch_in=None,
                         full=True) %}
{%- if wait_for_database_creation is none %}
{%- set  wait_for_database_creation = True %}
{%- endif %}
{%- if not watch_in %}
{%- set watch_in = [] %}
{%- endif %}
{%- if not watch %}
{%- set watch = [] %}
{%- endif %}
{%- if not dbs %}
{%- set dbs = [] %}
{%- endif %}
{%- if db and not db in dbs %}
{%- do dbs.append(db) %}
{%- endif %}
{%- if not versions %}
{%- set versions = [services.defaultPgVersion] %}
{%- endif %}
{%- if version and not version in versions%}
{%- do versions.append(version) %}
{%- endif %}
{% for version in versions %}
{%  for db in dbs %}
{%    for ext in exts %}
{% set extidx = loop.index0 %}
{{version}}-{{db}}-{{ext}}-makina-postgresql:
  mc_postgres_extension.present:
    {% if wait_for_database_creation or watch or (extidx > 0) %}
    - watch:
      {% if wait_for_database_creation %}
      - mc_proxy: {{version}}-{{db}}-makina-postgresql-database-post-hook
      {% endif %}
      {% for w in watch %}
      - {{ w }}
      {% endfor %}
      {% if extidx > 0 %}
      - mc_postgres_extension: {{version}}-{{db}}-{{exts[extidx-1]}}-makina-postgresql
      {% endif %}
    {% endif %}
    - watch_in:
      {% if wait_for_database_creation %}
      - mc_proxy: {{version}}-{{db}}-makina-postgresql-database-endpost-hook
      {% endif %}
      - mc_proxy: {{ orchestrate[version]['postdb'] }}
      {% for w in watch_in %}
      - {{ w }}
      {% endfor %}
    - user: {{ user }}
    - name: {{ext}}
    - pg_version: {{version}}
    - maintenance_db: {{db}}
    - db_host: {{db_host if db_host != None else 'null'}}
    - db_port: {{db_port if db_port != None else 'null'}}
{%    endfor%}
{%  endfor%}
{% endfor%}
{% endmacro %}

{% macro install_pg_ext(ext,
                        db=None,
                        dbs=None,
                        wait_for_database_creation=None,
                        versions=None,
                        version=None,
                        user=default_user,
                        db_host=None,
                        db_port=None,
                        watch=None,
                        watch_in=None,
                        full=True) %}
{{ install_pg_exts([ext],
                   db=db,
                   dbs=dbs,
                   wait_for_database_creation=None,
                   user=user,
                   version=version,
                   versions=versions,
                   db_host=db_host,
                   db_port=db_port,
                   watch_in=watch_in,
                   watch=watch,
                   full=full) }}
{% endmacro %}

{% macro postgresql_base(full=True) %}
{%- if full %}
{%- if grains['os_family'] in ['Debian'] %}
pgsql-repo:
  pkgrepo.managed:
    - name: deb http://apt.postgresql.org/pub/repos/apt/ {{localsettings.lts_dist}}-pgdg main
    - file: {{ locs.conf_dir }}/apt/sources.list.d/pgsql.list
    - keyid: 'ACCC4CF8'
    - keyserver: {{localsettings.keyserver }}
    - require:
      - mc_proxy: {{orchestrate['base']['prebase']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postbase']}}

{%- endif %}
postgresql-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
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
      - mc_proxy: {{orchestrate['base']['prebase']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postbase']}}
    {% endif %}
{% endif %}

{% for pgver in services.pgVers %}
postgresql-pg_hba-conf-{{pgver}}:
  file.managed:
    - name: /etc/postgresql/{{pgver}}/main/pg_hba.conf
    - source: salt://makina-states/files/etc/postgresql/pg_hba.conf
    - user: {{default_user}}
    - mode: 750
    - group: root
    - template: jinja
    - defaults:
      data: {{services.pgSettings.pg_hba|yaml}}
    {% if full %}
    - require:
      - pkg: postgresql-pkgs
    {% endif %}
    - watch_in:
      - service: makina-postgresql-service-reload

append-to-pg-hba-{{pgver}}-block:
  file.blockreplace:
    - name: /etc/postgresql/{{pgver}}/main/pg_hba.conf
    - marker_start: "#-- start salt managed zonestart -- PLEASE, DO NOT EDIT"
    - marker_end: "#-- end salt managed zonestart --"
    - content: ''
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - require:
        - file: postgresql-pg_hba-conf-{{pgver}}
        {% if full %}
        - pkg: postgresql-pkgs
        {% endif %}
    - watch_in:
      - service: makina-postgresql-service-reload

{% endfor %}

{#-MAIN SERVICE RESTART/RELOAD watchers #}
makina-postgresql-service:
  service.running:
    - name: postgresql
    - watch:
      {%- if full %}
      - pkg: postgresql-pkgs
      {%- endif %}
      - mc_proxy: {{orchestrate['base']['prebase']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postbase']}}

makina-postgresql-service-reload:
  service.running:
    - name: postgresql
    - enable: True
    - reload: True
    - require:
      {%- if full %}
      - pkg: postgresql-pkgs
      {%- endif %}
      - mc_proxy: {{orchestrate['base']['prebase']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postbase']}}
    {# most watch requisites are linked here with watch_in #}
{% endmacro %}

{#-POSTGRESQL CLUSTER directories, users, database, grants #}
{%- macro postgresql_group(group,
                          superuser=None,
                          createroles=None,
                          login=True,
                          inherit=None,
                          groups=None,
                          createdb=None,
                          rolepassword='',
                          encrypted=None,
                          replication=None,
                          user=default_user,
                          db_host=None,
                          db_port=None,
                          version=services.defaultPgVersion,
                          full=True, suf='') %}
{%- if not groups %}{% set groups=[] %}{% endif %}
{{ version }}-{{ group }}-makina-postgresql-group{{suf}}:
   mc_postgres_group.present:
    - name: {{ group }}
    - createdb: {{ createdb if createdb != None else 'null'}}
    - createroles: {{ createroles if createroles != None else 'null'}}
    - encrypted: {{ encrypted if encrypted != None else 'null'}}
    - password: {{ rolepassword if rolepassword != None else 'null'}}
    - superuser: {{ superuser if superuser != None else 'null'}}
    - replication: {{ replication if replication != None else 'null'}}
    - login: {{ login if login != None}}
    - user: {{ user }}
    - pg_version: {{version}}
    - db_host: {{db_host if db_host != None else 'null'}}
    - db_port: {{db_port if db_port != None else 'null'}}
    - require:
      - mc_proxy: {{orchestrate[version]['pregroup']}}
      - mc_proxy: {{orchestrate['base']['postbase']}}
    - require_in:
      - mc_proxy: {{orchestrate[version]['postgroup']}}
{% endmacro %}

{# Create a database, and an owner group which owns it #}
{%- macro postgresql_db(db,
                        owner=None,
                        tablespace='pg_default',
                        template='template1',
                        wait_for_template=True,
                        encoding='utf8',
                        user=default_user,
                        version=services.defaultPgVersion,
                        extensions=None,
                        full=True) -%}
{# group name is by default the db name #}
{% if not extensions %}
{% set extensions = [] %}
{% endif %}
{%- if not owner -%}
{%-   set owner = '%s_owners' % db %}
{%- endif -%}
{{ postgresql_group(owner, user=user, login=True) }}
{{version}}-{{ db }}-makina-postgresql-database:
  mc_postgres_database.present:
    - name: {{ db }}
    - encoding: {{ encoding }}
    - owner: {{ owner }}
    - template: {{template }}
    - tablespace: {{ tablespace }}
    - pg_version: {{version}}
    - user: {{ user }}
    - require:
      - mc_proxy: {{orchestrate[version]['predb']}}
      - mc_proxy: {{orchestrate['base']['postbase']}}
      {% if template not in ['template0', 'template1'] and wait_for_template %}
      - mc_proxy: {{version}}-{{ template }}-makina-postgresql-database-post-hook
      {% endif %}

{{ version }}-{{ owner }}-groups-makina-postgresql-grant:
  cmd.run:
    - name: echo "GRANT ALL PRIVILEGES ON DATABASE {{ db }} TO {{ owner }};"|psql-{{version}}
    - user: {{ user }}
    - require:
      - mc_postgres_database: {{version}}-{{ db }}-makina-postgresql-database

{#
# needed for extensions to be scheduled on sub databases, eg we install postgis, and postgis_database
# postgis is the postgis_database template.
# and postgis_database needs to be installed only and only after postgis extensions have been installed
#}
{{version}}-{{ db }}-makina-postgresql-database-post-hook:
  mc_proxy.hook:
    - watch:
      - cmd: {{ version }}-{{ owner }}-groups-makina-postgresql-grant

{{ install_pg_ext('adminpack', db=db, version=version, user=default_user) }}

{{version}}-{{ db }}-makina-postgresql-database-endpost-hook:
  mc_proxy.hook:
    - watch:
      - mc_proxy: {{version}}-{{ db }}-makina-postgresql-database-post-hook
    - watch_in:
      - mc_proxy: {{orchestrate[version]['postdb'] }}
      - mc_proxy: {{orchestrate['base']['postinst'] }}

{% endmacro %}
{#- Create and grant privs to a postgresql user #}
{%- macro postgresql_user(name,
                         password,
                         groups=None,
                         db=None,
                         createdb=None,
                         inherit=None,
                         login=True,
                         superuser=None,
                         replication=None,
                         createroles=None,
                         encrypted=None,
                         user=default_user,
                         db_host=None,
                         db_port=None,
                         version=services.defaultPgVersion,
                         full=True) %}
{%- if not groups %}
{%-   set groups = [] %}
{%- endif %}
{# if db is providen, add user to db owners #}
{%- if db %}
{% do groups.append('{0}_owners'.format(db)) %}
{% endif %}
{#- create groups prior to user #}
{%- for group in groups %}
{{ postgresql_group(group, user=user, version=version, suf='-user') }}
{%- endfor %}
{{version}}-{{ name }}-makina-services-postgresql-user:
  mc_postgres_user.present:
    - name: {{name}}
    - superuser: {{superuser if superuser != None else 'null'}}
    - password: {{ password if password != None else 'null'}}
    - createdb: {{ createdb if createdb != None else 'null'}}
    - inherit: {{ inherit if inherit != None else 'null'}}
    - login: {{ login if login != None else 'null'}}
    - replication: {{ replication if replication != None else 'null'}}
    - encrypted: {{ encrypted if encrypted != None else 'null'}}
    - createroles: {{createroles if createroles != None else 'null'}}
    - groups: {{','.join(groups)}}
    - pg_version : {{version}}
    - db_host: {{db_host if db_host != None else 'null'}}
    - db_port: {{db_port if db_port != None else 'null'}}
    - runas: {{ user }}
    - require_in:
      - mc_proxy: {{orchestrate[version]['postuser']}}
    - require:
      - mc_proxy: {{orchestrate[version]['preuser']}}
      - mc_proxy: {{orchestrate['base']['postbase']}}
    - password: {{ password }}
{% endmacro %}
{%- macro postgresql_wrappers(full=True) %}
{%- if full %}
{%- for version in services.pgVers %}
pgwrapper-{{version}}-makina-postgresql:
  file.managed:
    - name: /usr/bin/pg-wrapper-{{version}}.sh
    - source: salt://makina-states/files/usr/bin/pg-wrapper.sh
    - template: jinja
    - mode: 755
    - require_in:
      - mc_proxy: {{orchestrate[version]['predb']}}
      - mc_proxy: {{orchestrate[version]['pregroup']}}
      - mc_proxy: {{orchestrate[version]['preuser']}}
    - context:
      version: {{version}}

{%- for binary in [
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
      - mc_proxy: {{orchestrate[version]['predb']}}
      - mc_proxy: {{orchestrate[version]['pregroup']}}
      - mc_proxy: {{orchestrate[version]['preuser']}}
    - require:
      - file: pgwrapper-{{version}}-makina-postgresql
    - context:
      version: {{ version }}
      binary: {{ binary }}
{%-  endfor %}
{%- endfor %}
{%- endif %}
{%- endmacro %}

{#- MAIN #}
{% macro do(full=True) %}
include:
  - makina-states.services.db.postgresql-hooks
  {%- if full %}
  - makina-states.services.backup.dbsmartbackup
  {%- endif %}
{{ postgresql_base(full=full) }}
{{ postgresql_wrappers(full=full) }}
{%- endmacro %}

{%- macro do_content_from_pillar(full=True) %}
{{ do(full=full) }}
{%- for version in services.pgVers %}
{%- for db, data in services.pgDbs.items() %}
{%-     set encoding=data.get('encoding', 'utf8') %}
{%-     set owner=data.get('owner', None) %}
{%-     set template=data.get('encoding', 'template0')%}
{%-     set tablespace=data.get('tablespace', 'pg_default')%}
{{     postgresql_db(db=db,
                     owner=owner,
                     tablespace=tablespace,
                     encoding=encoding,
                     version=version,
                     template=template,
                     full=full) }}
{%- endfor %}
{%- for user, data in services.postgresqlUsers.items() %}
{%-    set groups = data.get('groups', []) %}
{%-    set pw = data['password'] %}
{%-    set superuser = data.get('superuser', False) %}
{%-    set encrypted = data.get('encrypted', True) %}
{%-    set replication = data.get('replication', False) %}
{%-    set createdb = data.get('createdb', False) %}
{{     postgresql_user(name=user,
                       password=pw,
                       createdb=createdb,
                       groups=groups,
                       version=version,
                       encrypted=encrypted,
                       superuser=superuser,
                       replication=replication,
                       full=full) }}
{%- endfor %}
{%- endfor %}
{%- endmacro %}
{{ do_content_from_pillar(full=False)}}
# vim:set nofoldenable:
