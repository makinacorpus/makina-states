{#!
# Install a postgis enabled database usable as a teamplate for postgis projects
#}
{% import "makina-states/services/db/postgresql.sls" as pgsql with context %}
{%- set services = pgsql.services %}
{%- set localsettings = services.localsettings %}
{%- set nodetypes = services.nodetypes %}
{%- set locs = salt['mc_localsettings']()['locations'] %}
{{ salt['mc_macros.register']('services', 'gis.postgis') }}
{% macro do(full=True) %}
{%- set dbname = services.postgisDbName %}
include:
  - makina-states.services.db.postgresql-hooks
  {% if full -%}
  - makina-states.services.db.postgresql
  {%- endif %}
{% for postgisVer, pgvers in services.postgisVers.items() -%}
{%  for pgVer in pgvers -%}
{%    if pgVer in services.pgVers -%}
{%      if full -%}
prereq-postgis-{{pgVer}}-{{postgisVer}}:
  pkg.{{localsettings.installmode}}:
    - require_in:
      - mc_proxy: {{pgsql.orchestrate[pgVer]['pregroup']}}
      - mc_proxy: {{pgsql.orchestrate[pgVer]['predb']}}
    {%  if full -%}
    - require:
      - pkg: postgresql-pkgs
    {%- endif %}
    - pkgs:
      - python-virtualenv {# noop #}
      {% if grains['os_family'] in ['Debian'] %}
      - postgresql-{{pgVer}}-postgis-{{postgisVer}}
      - liblwgeom-dev
      - postgresql-{{pgVer}}-postgis-scripts
      {% endif %}
{%-     endif %}

{{ pgsql.postgresql_db(dbname, full=full) }}

{{ pgsql.install_pg_exts(
    ["postgis",
     "postgis_topology",
     "fuzzystrmatch",
     "postgis_tiger_geocoder"],
    db=dbname,
    full=full) }}
{%-    endif %}
{%-  endfor %}
{%- endfor %}
{%- endmacro %}
{{ do(full=False) }}
