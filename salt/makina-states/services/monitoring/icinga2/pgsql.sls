{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga2.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

{% if data.modules.ido2db.enabled %}
{% if 'pgsql' == data.modules.ido2db.database.type %}

{% import "makina-states/services/db/postgresql/init.sls" as pgsql with context %}

include:
  # if ido2db is enabled, install and configure the sgbd

  # install postgresql
  - makina-states.services.monitoring.icinga2.hooks
  {% if data.has_pgsql and data.create_pgsql %}
  - makina-states.services.db.postgresql
  {% else %}
  - makina-states.services.db.postgresql.hooks
  {% endif %}

icinga-check-pw:
  cmd.run:
    - name: test "x{{data.modules.ido2db.database.password}}" != "x"
    - require_in:
      - mc_proxy: icinga2-safe-checks

icinga2-cli-pkgs:
  pkg.installed:
    - pkgs: [postgresql-client]
    - watch:
      - mc_proxy: makina-postgresql-post-base
    - watch_in:
      - mc_proxy: icinga2-pre-install

{% if data.create_pgsql %}
# create database
{{ pgsql.postgresql_db(db=data.modules.ido2db.database.name) }}

# add user
{{ pgsql.postgresql_user(name=data.modules.ido2db.database.user,
                         password=data.modules.ido2db.database.password,
                         db=data.modules.ido2db.database.name) }}

{% endif %}

{% if data.modules.ido2db.enabled %}
{% if 'socket' in data.modules.ido2db.database.host %}
{% set uri = "postgresql://{0}:{1}@[{2}]/{3}".format(
  data.modules.ido2db.database.user,
  data.modules.ido2db.database.password,
  data.modules.ido2db.database.socket,
  data.modules.ido2db.database.name) %}
{% else %}
{% set uri = "postgresql://{0}:{1}@{2}:{3}/{4}".format(
  data.modules.ido2db.database.user,
  data.modules.ido2db.database.password,
  data.modules.ido2db.database.host,
  data.modules.ido2db.database.port,
  data.modules.ido2db.database.name) %}
{% endif %}
{% endif %}
# import schema
{% set tmpf = '/tmp/icinga2-ido.schema.sql' %}
icinga2-import-pgsql-schema:
  file.managed:
    - name: {{tmpf}}
    - source: salt://makina-states/files/etc/icinga2/schemas/icinga2-ido.pgsql-schema.sql
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - defaults:
      data: |
            {{sdata}}
  cmd.run:
    - name: psql "{{uri}}" -f "{{tmpf}}"
    # wait if pgsql in restarted
    - unless: |
              if [ x"$(echo "select * from icinga_commands;" | psql "{{uri}}" --set ON_ERROR_STOP=1;echo $?)" != "x0" ];then
                sleep 2
                echo "select * from icinga_commands;" | psql "{{uri}}" --set ON_ERROR_STOP=1
                exit ${?}
              fi
              exit 0
    - watch:
      - pkg: icinga2-cli-pkgs
      - file: icinga2-import-pgsql-schema
      - mc_proxy: makina-postgresql-post-base
      - mc_proxy: icinga2-safe-checks
    - watch_in:
      - mc_proxy: icinga2-pre-install
{% endif %}
{% endif %}
