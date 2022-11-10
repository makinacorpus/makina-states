{%- import "makina-states/services/db/postgresql/hooks.sls" as hooks with context %}
{#- see doc/ref/formulaes/services/db/postgresql.rst #}
{% set settings = salt['mc_pgsql.settings']() %}
{% set orchestrate = hooks.orchestrate %}

include:
  - makina-states.services.db.postgresql.hooks


{%- for version in settings.versions %}
pgwrapper-{{version}}-makina-postgresql:
  file.managed:
    - name: /usr/bin/pg-wrapper-{{version}}.sh
    - source: salt://makina-states/files/usr/bin/pg-wrapper.sh
    - template: jinja
    - mode: 755
    - require_in:
      - mc_proxy: {{orchestrate['base']['prebase']}}
      - mc_proxy: {{orchestrate[version]['predb']}}
      - mc_proxy: {{orchestrate[version]['pregroup']}}
      - mc_proxy: {{orchestrate[version]['preuser']}}
    - context:
      version: {{version}}
{%- for binary in [
 'vacuumdb', 'dropdb', 'clusterdb', 'reindexdb', 'pg_dump', 'pg_basebackup',
 'pg_receivexlog', 'psql', 'createdb', 'dropuser', 'pg_dumpall', 'createuser',
 'pg_restore', 'pg_isready', 'createlang', 'droplang'
] %}
pgwrapper-{{binary}}-{{version}}-makina-postgresql:
  file.managed:
    - name: /usr/bin/{{binary}}-{{version}}
    - source: salt://makina-states/files/usr/bin/pgbin-wrapper.sh
    - template: jinja
    - mode: 755
    - require_in:
      - mc_proxy: {{orchestrate['base']['prebase']}}
      - mc_proxy: {{orchestrate[version]['predb']}}
      - mc_proxy: {{orchestrate[version]['pregroup']}}
      - mc_proxy: {{orchestrate[version]['preuser']}}
    - require_in:
      - mc_proxy: pgsql-wrappers
    - require:
      - file: pgwrapper-{{version}}-makina-postgresql
    - context:
      version: {{ version }}
      binary: {{ binary }}
{%-  endfor %}
{%- endfor %}

pgsql-wrappers:
  mc_proxy.hook: []

