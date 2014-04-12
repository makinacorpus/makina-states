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
                        full=True) -%}
{# group name is by default the db name #}
{% if not extensions %}
{% set extensions = [] %}
{% endif %}
{%- if not owner -%}
{%-   set owner = '%s_owners' % db %}
{%- endif -%}
{{ groups.postgresql_group(owner, user=user, login=True) }}
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
