{% set locs = salt['mc_locations.settings']() %}
{% set icinga2Settings = salt['mc_icinga2.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](icinga2Settings) %}
{% import "makina-states/services/db/mysql/init.sls" as mysql with context %}
include:
  - makina-states.services.db.mysql.hooks
  - makina-states.services.monitoring.icinga2.hooks
  - makina-states.services.monitoring.icinga2.icingadb_common
{% if 'mysql' == icinga2Settings.modules.icingadb.database.type and icinga2Settings.modules.icingadb.enabled %}
  - makina-states.services.monitoring.icinga2.prerequisites
{# it's user job to make database available to icinga, this state inits only the schema #}
{% set uri = "--user='{0}' --password='{1}' --host='{2}' --port='{3}' {4}".format(
  icinga2Settings.modules.icingadb.database.user,
  icinga2Settings.modules.icingadb.database.password,
  icinga2Settings.modules.icingadb.database.host,
  icinga2Settings.modules.icingadb.database.port,
  icinga2Settings.modules.icingadb.database.name) %}
# import schema
icinga2-import-mysql-schema:
  cmd.run:
    - name: |-
        set -ex && mysql {{uri}} < /usr/share/icingadb/schema/mysql/schema.sql
    - unless: |
              {% set t = 'mysql {0}<<<"select * from downtime limit 1;"'.format(uri) %}
              if [ x"$({{t}};echo $?)" != "x0" ];then sleep 2;{{t}};exit $?;fi
              exit 0
    - watch:
      - mc_proxy: icingadb-presetup
      - mc_proxy: mysql-setup-access
      - mc_proxy: icinga2-safe-checks
    - watch_in:
      - mc_proxy: icingadb-postsetup
{% endif %}
