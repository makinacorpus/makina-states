{% import "makina-states/services/db/postgresql.sls" as pgsql with context %}
{% set services = pgsql.services %}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set locs = localsettings.locations %}

{{ services.register('gis.postgis') }}

include:
  - makina-states.services.db.postgresql

{% set dbname = services.postgisDbName+'teste' %}

{% for postgisVer, pgvers in services.postgisVers.items() %}
{%  for pgVer in pgvers %}
{%    if pgVer in services.pgVers %}
prereq-postgis-{{pgVer}}-{{postgisVer}}:
  pkg.installed:
    - require_in:
      - cmd: {{pgsql.orchestrate[pgVer]['pregroup']}}
      - cmd: {{pgsql.orchestrate[pgVer]['predb']}}
    - require:
      - pkg: postgresql-pkgs
    - pkgs:
      - python-virtualenv {# noop #}
      {% if grains['os_family'] in ['Debian'] %}
      - postgresql-{{pgVer}}-postgis-{{postgisVer}}
      - liblwgeom-dev
      - postgresql-{{pgVer}}-postgis-scripts
      {% endif %}

{{ pgsql.postgresql_db(dbname) }}

{{ pgsql.install_pg_exts(
    ["postgis",
     "postgis_topology",
     "fuzzystrmatch",
     "postgis_tiger_geocoder"],
    db=dbname) }}
{%    endif %}
{%  endfor %}
{% endfor %}
