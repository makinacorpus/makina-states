{#- see doc/ref/formulaes/services/db/resql.rst #}
{%- import "makina-states/services/db/postgresql/hooks.sls" as hooks with context %}
include:
  - makina-states.services.db.postgresql.hooks

{% set settings = salt['mc_pgsql.settings']() %}
{%- set default_user = settings.user %}
{% set orchestrate = hooks.orchestrate %}
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
                          version=settings.defaultPgVersion,
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
    - unless: echo "SELECT rolname FROM pg_roles;" | su {{user}} -c "psql -t -A -F"---" postgres" | egrep -q "^{{group}}$"
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
