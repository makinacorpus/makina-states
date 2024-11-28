{% set locs = salt['mc_locations.settings']() %}
{% set icinga2Settings = salt['mc_icinga2.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](icinga2Settings) %}
{% if icinga2Settings.modules.icingadb.enabled %}
{% import "makina-states/services/db/postgresql/init.sls" as pgsql with context %}
include:
  - makina-states.services.monitoring.icinga2.hooks
  - makina-states.services.db.postgresql.hooks
  - makina-states.services.monitoring.icinga2.icingadb_common
{% if 'pgsql' == icinga2Settings.modules.icingadb.database.type and icinga2Settings.modules.icingadb.enabled %}
  - makina-states.services.monitoring.icinga2.prerequisites
{# it's user job to make database available to icinga, this state inits only the schema #}
{% if 'socket' in icinga2Settings.modules.icingadb.database.host %}
{% set uri = "postgresql://{0}:{1}@[{2}]/{3}".format(
  icinga2Settings.modules.icingadb.database.user,
  icinga2Settings.modules.icingadb.database.password,
  icinga2Settings.modules.icingadb.database.socket,
  icinga2Settings.modules.icingadb.database.name) %}
{% else %}
{% set uri = "postgresql://{0}:{1}@{2}:{3}/{4}".format(
  icinga2Settings.modules.icingadb.database.user,
  icinga2Settings.modules.icingadb.database.password,
  icinga2Settings.modules.icingadb.database.host,
  icinga2Settings.modules.icingadb.database.port,
  icinga2Settings.modules.icingadb.database.name) %}
{% endif %}
# import schema
icinga2-import-pgsql-dbsetup:
  cmd.run:
    - name: |-
        set -ex && psql --set ON_ERROR_STOP=1 "{{uri}}" icingadb <<<'CREATE EXTENSION IF NOT EXISTS citext;'
    - unless: |
              {% set t = 'psql --set ON_ERROR_STOP=1 "{0}" icingadb <<<"select * from pg_extension;"|grep -q citext'.format(uri) %}
              if [ x"$({{t}};echo $?)" != "x0" ];then sleep 2;{{t}};exit $?;fi
              exit 0
    - watch:
      - mc_proxy: icingadb-presetup
      - mc_proxy: makina-postgresql-post-base
      - mc_proxy: icinga2-safe-checks
    - watch_in:
      - mc_proxy: icingadb-postsetup
icinga2-import-pgsql-schema:
  cmd.run:
    - name: |-
        set -ex && psql --set ON_ERROR_STOP=1 "{{uri}}" < /usr/share/icingadb/schema/pgsql/schema.sql
    - unless: |
              {% set t = 'psql --set ON_ERROR_STOP=1 "{0}" icingadb <<<"select * from downtime limit 1;"'.format(uri) %}
              if [ x"$({{t}};echo $?)" != "x0" ];then sleep 2;{{t}};exit $?;fi
              exit 0
    - watch:
      - cmd: icinga2-import-pgsql-dbsetup
      - mc_proxy: icingadb-presetup
      - mc_proxy: makina-postgresql-post-base
      - mc_proxy: icinga2-safe-checks
    - watch_in:
      - mc_proxy: icingadb-postsetup
{% endif %}
