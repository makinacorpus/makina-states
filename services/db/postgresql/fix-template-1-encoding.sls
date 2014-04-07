{%- import "makina-states/services/db/postgresql/groups.sls" as groups with context %}
{%- import "makina-states/services/db/postgresql/extensions.sls" as ext with context %}
{%- import "makina-states/services/db/postgresql/hooks.sls" as hooks with context %}

{% set settings = salt['mc_pgsql.settings']() %}
{% set encoding = settings['encoding'] %}
{% set locale = settings['locale'] %}
{%- set localsettings = salt['mc_localsettings.settings']() %}
{%- set locs = localsettings.locations %}
{%- set default_user = settings.user %}
{% set orchestrate = hooks.orchestrate %}
include:
  - makina-states.services.db.postgresql.hooks
{#
# many database installers create the template1
# with latin1 encoding making then difficult to handle
# utf-8 db creation from this template
# we then recreate template1 with right lctype !
#}
{% macro fix(version) %}
{% set tmpf = '/tmp/psql.{0}fix.sql'.format(version) %}
makina-postgresql-{{version}}-fix-template1:
  file.managed:
    - name: {{tmpf}}
    - source: ''
    - user: {{default_user}}
    - contents: |
                update pg_database set datallowconn = TRUE where datname = 'template0';
                \c template0
                update pg_database set datistemplate = FALSE where datname = 'template1';
                drop database template1;
                create database template1 with template = template0 encoding = '{{encoding}}' LC_CTYPE = '{{locale}}' LC_COLLATE = '{{locale}}';
                update pg_database set datistemplate = TRUE where datname = 'template1';
                \c template1
                update pg_database set datallowconn = FALSE where datname = 'template0';
  cmd.run:
    - user: {{default_user}}
    - name: psql-{{version}} template1 -f {{tmpf}}
    - unless: psql -t -A -F';;;' -c'\l'|egrep '^template1;;;'|egrep -i 'utf.?8;;;$'
    - require:
      - file: makina-postgresql-{{version}}-fix-template1
      - mc_proxy: {{orchestrate['base']['presetup']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postbase']}}
makina-postgresql-{{version}}-fix-template1-cleanup:
  file.absent:
    - name: {{tmpf}}
    - require:
      - cmd: makina-postgresql-{{version}}-fix-template1
{% endmacro %}
{%- for version in settings.versions %}
{{ fix(version) }}
{%- endfor %}
