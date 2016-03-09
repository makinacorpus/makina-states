{%- import "makina-states/services/db/postgresql/hooks.sls" as hooks with context %}
{#- see doc/ref/formulaes/services/db/postgresql.rst #}
{% set settings = salt['mc_pgsql.settings']() %}
{%- set default_user = settings.user %}
{%- set orchestrate = hooks.orchestrate %}

include:
  - makina-states.services.db.postgresql.hooks

{% for pgver in settings.versions %}
postgresql-pg_hba-conf-{{pgver}}:
  file.managed:
    - name: /etc/postgresql/{{pgver}}/main/pg_hba.conf
    - source: salt://makina-states/files/etc/postgresql/pg_hba.conf
    - user: {{default_user}}
    - mode: 750
    - group: root
    - template: jinja
    - defaults:
      data: |
            {{salt['mc_utils.json_dump'](settings.pg_hba)}}
    - require:
      - mc_proxy: {{orchestrate['base']['postpkg']}}
    - watch_in:
      - mc_proxy: {{orchestrate['base']['postbase']}}
      - mc_proxy: pgsql-service-restart-hook

append-to-pg-hba-{{pgver}}-block:
  file.blockreplace:
    - name: /etc/postgresql/{{pgver}}/main/pg_hba.conf
    - marker_start: "#-- start salt managed zonestart -- PLEASE, DO NOT EDIT"
    - marker_end: "#-- end salt managed zonestart --"
    - content: ''
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - require:
        - file: postgresql-pg_hba-conf-{{pgver}}
    - watch_in:
      - mc_proxy: {{orchestrate['base']['postbase']}}
      - mc_proxy: pgsql-service-restart-hook
{% endfor %}
