{# install the postgis pgsql template/extension #}
{%- import "makina-states/services/db/postgresql/init.sls" as pgsql with context %}
include:
  - makina-states.services.db.postgresql.hooks
{% set pgSettings = salt['mc_pgsql.settings']() %}
{% if pgSettings.postgis_pkgs%}
makinastatees-postgis-prereq:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - require_in:
      {% for pgVer in pgSettings.versions %}
      - mc_proxy: {{pgsql.orchestrate[pgVer]['pregroup']}}
      - mc_proxy: {{pgsql.orchestrate[pgVer]['predb']}}
      {% endfor %}
    - require:
      - pkg: postgresql-pkgs
    - pkgs: {{pgSettings.postgis_pkgs}}
{% endif%}
