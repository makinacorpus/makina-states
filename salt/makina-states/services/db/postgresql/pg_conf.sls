{%- import "makina-states/services/db/postgresql/hooks.sls" as hooks with context %}
{#- see doc/ref/formulaes/services/db/postgresql.rst #}
{% set settings = salt['mc_pgsql.settings']() %}
{%- set default_user = settings.user %}
{%- set orchestrate = hooks.orchestrate %}

include:
  - makina-states.services.db.postgresql.hooks

{% for pgver in settings.versions %}
postgresql-pg_conf-conf-{{pgver}}-inc-conf:
  file.managed:
    - name: /etc/postgresql/{{pgver}}/main/conf.d/empty.conf
    - contents: '#empty'
    - source: ''
    - user: {{default_user}}
    - mode: 750
    - makedirs: true
    - group: root
    - template: jinja
    - require:
      - mc_proxy: {{orchestrate['base']['postpkg']}}
    - watch_in:
      - mc_proxy: {{orchestrate['base']['postbase']}}
      - service: makina-postgresql-service-reload

postgresql-pg_conf-conf-{{pgver}}:
  file.managed:
    - name: /etc/postgresql/{{pgver}}/main/postgresql.conf
    - source: salt://makina-states/files/etc/postgresql/postgresql.conf
    - user: {{default_user}}
    - mode: 750
    - group: root
    - template: jinja
    - defaults:
      version: {{pgver}}
      conf: |
            {{salt['mc_utils.json_dump'](settings.pg_conf[pgver])}}
      data: |
            {{salt['mc_utils.json_dump'](settings)}}
    - require:
      - mc_proxy: {{orchestrate['base']['postpkg']}}
    - watch_in:
      - mc_proxy: {{orchestrate['base']['postbase']}}
      - service: makina-postgresql-service-reload

# caused too much restart pb
# use confdir in any other case
#append-to-pg-conf-{{pgver}}-block:
#  file.blockreplace:
#    - name: /etc/postgresql/{{pgver}}/main/postgresql.conf
#    - marker_start: "#-- start salt managed zonestart -- PLEASE, DO NOT EDIT"
#    - marker_end: "#-- end salt managed zonestart --"
#    - content: ''
#    - append_if_not_found: True
#    - backup: '.bak'
#    - show_changes: True
#    - require:
#        - file: postgresql-pg_conf-conf-{{pgver}}
#    - watch_in:
#      - mc_proxy: {{orchestrate['base']['postbase']}}
#      - service: makina-postgresql-service-reload
{% endfor %}
