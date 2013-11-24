# define in pillar a postgresql pillar entry:
# goal of this state is:
#   - to have a working up & running postgresql server
#   - setup basic db, roles & users
#
# By default the owner of the database is a groupwith the same name suffixed witrh owner for the user to be added to
# We assign then users to this group
# Define the user to run psql command as:
# makina.postgresql.user: foo (default: postgres)
#
# Define a database and its owner as follow (see salt.states.postgres_database.present)
# bar-makina-postgresql:
#   name: foo (opt, default; 'bar')
#   encoding: foo (opt, default; utf8)
#   template: foo (opt, default; template0)
#   tablespace: foo (opt, default; pg_default)
# This will create a 'bar' database owned by the group 'bar-owners'
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
{% set psql_user = salt['config.get']('makina.postgresql.user', 'postgres') %}

postgresql-pkgs:
  pkg.installed:
    - names:
      - postgresql
      - libpq-dev
      - python-virtualenv

makina-postgresql-service:
  service.running:
    - name: postgresql
    - require:
      - pkg: postgresql-pkgs
    - watch:
      - pkg: postgresql-pkgs


{% for dbk, data in pillar.items() %}
{% if dbk.endswith('-makina-postgresql') %}
{% set db = data.get('name', dbk.split('-makina-postgresql')[0]) %}
{% set enc=data.get('encoding', 'utf8') %}
{% set template=data.get('encoding', 'template0')%}
{% set tablespace=data.get('tablesplace', 'pg_default')%}

{{db}}_owners-makina-postresql-group:
   postgres_group.present:
    - name: {{db}}_owners
    - runas: {{psql_user}}
    - require:
      - service: makina-postgresql-service

{{db}}_owners-makina-postgresql-group-login:
  cmd.run:
    - name: echo "ALTER ROLE {{db}}_owners WITH LOGIN;"|psql
    - user: {{psql_user}}
    - require:
      - postgres_group: {{db}}_owners-makina-postresql-group

{{db}}-makina-postgresql-database:
  cmd.run:
    - name: createdb {{db}} -E {{enc}} -O {{db}}_owners -T {{template }} -D {{tablespace}}
    - unless: test "$(psql -l|awk '{print $1}'|grep -w {{db}}|wc -l)" != "0"
    - user: {{psql_user}}
    - require:
      - service: makina-postgresql-service
      - postgres_group: {{db}}_owners-makina-postresql-group

{{db}}-owners-makina-postresql-grant:
  cmd.run:
    - name: echo "GRANT ALL PRIVILEGES ON DATABASE {{db}} TO {{db}}_owners;"|psql
    - user: {{psql_user}}
    - require:
      - postgres_group: {{db}}_owners-makina-postresql-group
      - cmd: {{db}}-makina-postgresql-database
{% endif %}
{% endfor %}

{% for userk, data in pillar.items() %}
{% if userk.endswith('-makina-postgresql-user') %}
{% set user = data.get('name', userk.split('-makina-postgresql-user')[0]) %}
{% set groups = data.get('groups', []) %}
{% set pw = data['password'] %}
{% set superuser = data.get('superuser', False) %}
{% set encrypted = data.get('encrypted', True) %}
{% set replication = data.get('replication', False) %}
{% set createdb = data.get('createdb', False) %}
{{user}}_database_user:
  postgres_user.present:
    - name: {{ user }}
    - password: {{pw}}
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
#  cmd.run:
#    - name: echo "ALTER USER {{ user }} WiTH ENCRYPTED PASSWORD '{{pw}}';"|psql
#    - user: {{psql_user}}
#    - require:
#      - postgres_user: {{user}}_database_user
{% endif %}
{% endfor %}
