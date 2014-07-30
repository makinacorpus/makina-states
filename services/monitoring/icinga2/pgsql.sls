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

{% if data.create_pgsql %}
# create database
{{ pgsql.postgresql_db(db=data.modules.ido2db.database.name) }}

# add user
{{ pgsql.postgresql_user(name=data.modules.ido2db.database.user,
                         password=data.modules.ido2db.database.password,
                         db=data.modules.ido2db.database.name) }}

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
    {% if 'socket' in data.modules.ido2db.database %}
    - name: psql "postgresql://{{data.modules.ido2db.database.user}}:{{data.modules.ido2db.database.password}}@[{{data.modules.ido2db.database.socket}}]/{{data.modules.ido2db.database.name}}" -f "{{tmpf}}"
    {% else %}
    - name: psql "postgresql://{{data.modules.ido2db.database.user}}:{{data.modules.ido2db.database.password}}@{{data.modules.ido2db.database.host}}:{{data.modules.ido2db.database.port}}/{{data.modules.ido2db.database.name}}" -f "{{tmpf}}"
    {% endif %}
    {% if 'socket' in data.modules.ido2db.database %}
    - unless: echo "select * from icinga_commands;" | psql "postgresql://{{data.modules.ido2db.database.user}}:{{data.modules.ido2db.database.password}}@[{{data.modules.ido2db.database.socket}}]/{{data.modules.ido2db.database.name}}"
    {% else %}
    - unless: echo "select * from icinga_commands;" | psql "postgresql://{{data.modules.ido2db.database.user}}:{{data.modules.ido2db.database.password}}@{{data.modules.ido2db.database.host}}:{{data.modules.ido2db.database.port}}/{{data.modules.ido2db.database.name}}"
    {% endif %}
    - watch:
      - file: icinga2-import-pgsql-schema
      - mc_proxy: makina-postgresql-post-base
    - watch_in:
      - mc_proxy: icinga2-pre-install
{% endif %}
{% endif %}
