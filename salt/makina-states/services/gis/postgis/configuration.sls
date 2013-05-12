{% import "makina-states/services/db/postgresql/init.sls" as pgsql with context %}
{%- set locs = salt['mc_locations.settings']() %}
{% set pgSettings = salt['mc_pgsql.settings']() %}
{%- set dbname = pgSettings.postgis_db %}
include:
  - makina-states.services.db.postgresql.hooks
{% for postgisVer, pgvers in pgSettings.postgis.items() -%}
{%  for pgVer in pgvers -%}
{%    if pgVer in pgSettings.versions -%}
{{ pgsql.postgresql_db(dbname, full=full, version=pgVer, suf='postgis-{0}'.format(postgisVer)) }}
{{ pgsql.install_pg_exts(
    ["postgis",
     "postgis_topology",
     "fuzzystrmatch",
     "postgis_tiger_geocoder"],
    db=dbname,
    versions=[pgVer],
    full=full) }}
{%-    endif %}
{%-  endfor %}
{%- endfor %}
