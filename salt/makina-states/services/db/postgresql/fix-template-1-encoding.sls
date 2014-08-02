{%- import "makina-states/services/db/postgresql/groups.sls" as groups with context %}
{%- import "makina-states/services/db/postgresql/extensions.sls" as ext with context %}
{%- import "makina-states/services/db/postgresql/hooks.sls" as hooks with context %}

{% set settings = salt['mc_pgsql.settings']() %}
{% set encoding = settings['encoding'] %}
{% set locale = settings['locale'] %}
{%- set default_user = settings.user %}
{% set orchestrate = hooks.orchestrate %}
include:
  - makina-states.services.db.postgresql.hooks
  - makina-states.services.db.postgresql.wrappers
{#
# many database installers create the template1
# with latin1 encoding making then difficult to handle
# utf-8 db creation from this template
# we then recreate template1 with right lctype !
#}
{% macro fix(version, db='template1', template='template1') %}
{% set tmpf = '/tmp/psql.{0}-{1}-fix.sql'.format(version, db) %}
{% if db == 'template1' %}
{%  set template = 'template0' %}
{% endif %}
makina-postgresql-{{version}}-fix-{{db}}:
  file.managed:
    - require:
      - mc_proxy: pgsql-wrappers
    - name: {{tmpf}}
    - source: ''
    - user: {{default_user}}
    - contents: |
                {% if db == 'template1' %}
                update pg_database set datallowconn = TRUE where datname = 'template0';
                update pg_database set datistemplate = FALSE where datname = 'template1';
                {% endif %}
                \c {{template}}
                drop database {{db}};
                create database {{db}} with template = {{template}} encoding = '{{encoding}}' LC_CTYPE = '{{locale}}' LC_COLLATE = '{{locale}}';
                \c {{db}}
                {% if db == 'postgis' %}
                create extension hstore;
                create extension postgis;
                create extension postgis_topology;
                create extension fuzzystrmatch;
                create extension postgis_tiger_geocoder;
                {% endif %}
                {% if db == 'template1' %}
                update pg_database set datistemplate = TRUE where datname = 'template1';
                update pg_database set datallowconn = FALSE where datname = 'template0';
                {% endif %}
    {% if db in ['template0', 'template1'] %}
    - require:
      - mc_proxy: {{orchestrate['base']['presetup']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postbase']}}
    {%else%}
    - require:
      - mc_proxy: {{orchestrate[version]['postdb']}}
    - require_in:
      - mc_proxy: {{orchestrate[version]['preuser']}}
    {%endif%}
  cmd.run:
    - user: {{default_user}}
    - name: psql-{{version}} {{db}} -f {{tmpf}}
    - unless: |
              # either locale is good => skip
              psql -t -A -F';;;' -c'\l'|egrep '^{{db}};;;'|egrep -i "{{locale[0:2]}}"|egrep -i 'utf.?8;;;$' ||\
              # or database does not exist => skip
              psql -t -A -F';;;' -c'\l'|awk -F";" '{print $1}'|egrep -vq "^{{db}}$"
    {% if db in ['template0', 'template1'] %}
    - require:
      - file: makina-postgresql-{{version}}-fix-{{db}}
      - mc_proxy: {{orchestrate['base']['presetup']}}
    - require_in:
      - mc_proxy: {{orchestrate['base']['postbase']}}
    {%else%}
    - require:
      - file: makina-postgresql-{{version}}-fix-{{db}}
      - mc_proxy: {{orchestrate[version]['postdb']}}
    - require_in:
      - mc_proxy: {{orchestrate[version]['preuser']}}
    {%endif%}
makina-postgresql-{{version}}-fix-{{db}}-cleanup:
  file.absent:
    - name: {{tmpf}}
    - require:
      - cmd: makina-postgresql-{{version}}-fix-{{db}}
{% endmacro %}
{%- for version in settings.versions %}
{{ fix(version, db='template1') }}
{{ fix(version, db='postgis') }}
{%- endfor %}
