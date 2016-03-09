{#- see doc/ref/formulaes/services/db/resql.rst #}
{%- import "makina-states/services/db/postgresql/hooks.sls" as hooks with context %}
{% set settings = salt['mc_pgsql.settings']() %}
{%- set default_user = settings.user %}
{% set orchestrate = hooks.orchestrate %}

include:
  - makina-states.services.db.postgresql.hooks

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
{%- set versions = [settings.defaultPgVersion] %}
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
