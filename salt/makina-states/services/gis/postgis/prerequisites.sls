{# install the postgis pgsql template/extension #}
{%- import "makina-states/services/db/postgresql/init.sls" as pgsql with context %}
include:
  - makina-states.services.db.postgresql.hooks
{% set pgSettings = salt['mc_pgsql.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}
{%- set dbname = pgSettings.postgis_db %}
{% for postgisVer, pgvers in pgSettings.postgis.items() -%}
{%  for pgVer in pgvers -%}
{%    if pgVer in pgSettings.versions -%}
prereq-postgis-{{pgVer}}-{{postgisVer}}:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - require_in:
      - mc_proxy: {{pgsql.orchestrate[pgVer]['pregroup']}}
      - mc_proxy: {{pgsql.orchestrate[pgVer]['predb']}}
    - require:
      - pkg: postgresql-pkgs
    - pkgs:
      - python-virtualenv {# noop #}
      {% if grains['os_family'] in ['Debian'] %}
      - postgresql-{{pgVer}}-postgis-{{postgisVer}}
      {% if not pgSettings.xenial_onward %}- liblwgeom-dev{% endif%}
      - postgresql-{{pgVer}}-postgis-scripts
      {% endif %}
{%-    endif %}
{%-  endfor %}
{%- endfor %}
