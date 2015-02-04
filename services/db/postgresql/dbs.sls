{#- see doc/ref/formulaes/services/db/postgresql.rst #}
{%- import "makina-states/services/db/postgresql/groups.sls" as groups with context %}
{%- import "makina-states/services/db/postgresql/extensions.sls" as ext with context %}
{%- import "makina-states/services/db/postgresql/hooks.sls" as hooks with context %}

{% set settings = salt['mc_pgsql.settings']() %}
{%- set default_user = settings.user %}
{% set orchestrate = hooks.orchestrate %}

include:
  - makina-states.services.db.postgresql.hooks
{% set dencoding = settings['encoding'] %}
{% set dlocale = settings['locale'] %}

{# Create a database, and an owner group which owns it #}
{%- macro postgresql_db(db,
                        owner=None,
                        tablespace='pg_default',
                        template='template1',
                        wait_for_template=True,
                        encoding=dencoding,
                        lc_collate = dlocale,
                        lc_ctype = dlocale,
                        user=default_user,
                        version=settings.defaultPgVersion,
                        extensions=None,
                        full=True, suf='') -%}
{# group name is by default the db name #}
{% if not extensions %}
{% set extensions = [] %}
{% endif %}
{%- if not owner -%}
{%-   set owner = '%s_owners' % db %}
{%- endif -%}
{{ groups.postgresql_group(owner, user=user, login=True, suf=suf) }}
{{version}}-{{ db }}-makina-postgresql-database:
  mc_postgres_database.present:
    - name: {{ db }}
    - lc_ctype: {{ lc_ctype }}
    - lc_collate: {{ lc_collate }}
    - encoding: {{ encoding }}
    - owner: {{ owner }}
    - template: {{template }}
    - tablespace: {{ tablespace }}
    - pg_version: {{version}}
    # if database exists
    # do not run as default locate can change over time and make this
    # state fail whenever the database already easist and works well
    - onlyif: test "x$(echo "SELECT datname FROM pg_database;"|su postgres -c "psql -t -A -F"---""|egrep -q "^{{db}}$";echo $?)" = "x1"
    - user: {{ user }}
    - require:
      - mc_proxy: {{orchestrate[version]['predb']}}
      - mc_proxy: {{orchestrate['base']['postbase']}}
      {% if (
          template not in ['template0', 'template1']
          and wait_for_template
      )%}
      - mc_proxy: {{version}}-{{ template }}-makina-postgresql-database-post-hook
      {% endif %}

{{ version }}-{{ owner }}-groups-makina-postgresql-grant{{suf}}:
  cmd.run:
    - name: |
            set -e
            echo "GRANT ALL PRIVILEGES ON DATABASE {{ db }} TO {{ owner }};"|psql-{{version}} -v ON_ERROR_STOP=1 {{db}}
            echo "ALTER SCHEMA public OWNER TO {{ owner }};"|psql-{{version}} -v ON_ERROR_STOP=1 {{db}}
            echo "GRANT ALL PRIVILEGES ON SCHEMA public TO {{ owner }};"|psql-{{version}} -v ON_ERROR_STOP=1 {{db}}
    - user: {{ user }}
    - require:
      - mc_postgres_database: {{version}}-{{ db }}-makina-postgresql-database

{{ version }}-{{ owner }}-fix-owner{{suf}}:
  file.managed:
    - name: /etc/postgresql/{{version}}-{{db}}-owners.sql
    - mode: 0755
    - user: root
    - group: root
    - template: jinja
    - contents: |
                ALTER DATABASE {{db}} OWNER TO {{owner}};
                SELECT 'ALTER SCHEMA "' || n.NSPNAME || '" OWNER TO {{owner}};'
                FROM PG_CATALOG.PG_NAMESPACE n
                WHERE n.NSPNAME NOT ILIKE 'PG_%' AND n.NSPNAME NOT ILIKE 'INFORMATION_SCHEMA';
                SELECT 'ALTER TABLE "'|| schemaname || '"."' || tablename ||'" OWNER TO {{owner}};'
                FROM pg_tables WHERE NOT schemaname IN ('pg_catalog', 'information_schema')
                ORDER BY schemaname, tablename;
                SELECT 'ALTER SEQUENCE "'|| sequence_schema || '"."' || sequence_name ||'" OWNER TO {{owner}};'
                FROM information_schema.sequences WHERE NOT sequence_schema IN ('pg_catalog', 'information_schema')
                ORDER BY sequence_schema, sequence_name;
                SELECT 'ALTER VIEW "'|| table_schema || '"."' || table_name ||'" OWNER TO {{owner}};'
                FROM information_schema.views WHERE NOT table_schema IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name;
  cmd.run:
    - name: |
            set -e
            fic="/tmp/postgresql_{{version}}-{{db}}-do-owners.sql"
            psql-{{version}} -f "/etc/postgresql/{{version}}-{{db}}-owners.sql" -t -q -v ON_ERROR_STOP=1 {{db}} | grep ALTER > "${fic}"
            psql-{{version}} -f "${fic}" -v ON_ERROR_STOP=1 "{{db}}"
            rm -f "${fic}"
    - user: {{ user }}
    - watch:
      - file: {{ version }}-{{ owner }}-fix-owner{{suf}}
      - mc_proxy: {{orchestrate[version]['prefixowner'] }}
    - watch_in:
      - mc_proxy: {{orchestrate[version]['postfixowner'] }}

{#
# needed for extensions to be scheduled on sub databases, eg we install postgis, and postgis_database
# postgis is the postgis_database template.
# and postgis_database needs to be installed only and only after postgis extensions have been installed
#}
{{version}}-{{ db }}-makina-postgresql-database-post-hook:
  mc_proxy.hook:
    - watch:
      - cmd: {{ version }}-{{ owner }}-groups-makina-postgresql-grant{{suf}}

{{ ext.install_pg_ext('adminpack', db=db, version=version, user=default_user) }}
{{version}}-{{ db }}-makina-postgresql-database-endpost-hook:
  mc_proxy.hook:
    - watch:
      - mc_proxy: {{version}}-{{ db }}-makina-postgresql-database-post-hook
    - watch_in:
      - mc_proxy: {{orchestrate[version]['postdb'] }}
      - mc_proxy: {{orchestrate['base']['postinst'] }}

{% endmacro %}
{%- for version in settings.versions %}
{%- for db, data in settings.pgDbs.items() %}
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
{%- endfor %}
