{#- Create and grant privs to a postgresql user #}
{%- import "makina-states/services/db/postgresql/groups.sls" as groupsmac with context %}
{%- import "makina-states/services/db/postgresql/hooks.sls" as hooks with context %}
{% set settings = salt['mc_pgsql.settings']() %}
{% set orchestrate = hooks.orchestrate %}
{%- set default_user = settings.user %}
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
                         version=settings.defaultPgVersion,
                         full=True, suf='') %}
{%- if not groups %}
{%-   set groups = [] %}
{%- endif %}
{# if db is providen, add user to db owners #}
{%- if db %}
{%    set owners = '{0}_owners'.format(db)  %}
{%    if owners not in groups %}
{%      do groups.append(owners) %}
{%    endif %}
{% endif %}
{#- create groups prior to user #}
{%- for group in groups %}
{{ groupsmac.postgresql_group(group,
                              user=user,
                              version=version,
                              suf='-{0}{1}-user'.format(name, suf)) }}
{%- endfor %}
{{version}}-{{ name }}-makina-services-postgresql-user{{suf}}:
  mc_postgres_user.present:
    - name: {{name}}
    - superuser: {{superuser if superuser != None else 'null'}}
    - createdb: {{ createdb if createdb != None else 'null'}}
    - inherit: {{ inherit if inherit != None else 'null'}}
    - login: {{ login if login != None else 'null'}}
    - replication: {{ replication if replication != None else 'null'}}
    - encrypted: {{ encrypted if encrypted != None else 'null'}}
    - createroles: {{createroles if createroles != None else 'null'}}
    - unless: |
              echo 'select 1;' | psql-{{version}} -v ON_ERROR_STOP=1 \
                'postgresql://{{
                  name}}{{':{0}'.format(password) if password != None else ''}}@{{
                    db_host if db_host != None else '127.0.0.1'}}{{
                      ':{0}'.format(db_port) if db_port != None else ':5432'}}/postgres'
    {% if groups %}
    - groups: {{','.join(groups)}}
    {% endif %}
    - pg_version : {{version}}
    - db_host: {{db_host if db_host != None else 'null'}}
    - db_port: {{db_port if db_port != None else 'null'}}
    - user: {{ user }}
    - require_in:
      - mc_proxy: {{orchestrate[version]['postuser']}}
    - require:
      - mc_proxy: {{orchestrate[version]['preuser']}}
      - mc_proxy: {{orchestrate['base']['postbase']}}
    - password: {{ password if password != None else 'null'}}
{% endmacro %}

{%- for user, data in settings.postgresqlUsers.items() %}
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
