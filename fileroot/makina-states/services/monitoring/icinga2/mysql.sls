{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga2.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

{% if data.modules.ido2db.enabled %}
{% if 'mysql' == data.modules.ido2db.database.type %}

{% from 'makina-states/services/db/mysql/macros.sls' import mysql_base,mysql_db with context %}

include:
  # if ido2db is enabled, install and configure the sgbd

  # install mysql
  {% if data.has_mysql %}
  - makina-states.services.db.mysql
  {% else %}
  - makina-states.services.db.mysql.hooks
  {% endif %}

# add user
icinga2-create-mysql-user:
  mysql_database.present:
    - name: {{data.modules.ido2db.database.user}}

# create database
{{ mysql_db(
    db=data.modules.ido2db.database.name,
    user=data.modules.ido2db.database.user,
    password=data.modules.ido2db.database.password) }}

# import schema
{% set tmpf = '/tmp/icinga2-ido.schema.sql' %}
icinga2-import-mysql-schema:
  file.managed:
    - name: {{tmpf}}
    - source: salt://makina-states/files/etc/icinga2/schemas/icinga2-ido.mysql-schema.sql
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
  - name: mysql --socket="{{data.modules.ido2db.database.socket}}" --user="{{data.modules.ido2db.database.user}}" --password="{{data.modules.ido2db.database.password}}" "{{data.modules.ido2db.database.name}}" < "{{tmpf}}"
    {% else %}
    - name: mysql --host="{{data.modules.ido2db.database.host}}" --port="{{data.modules.ido2db.database.port}}" --user="{{data.modules.ido2db.database.user}}" --password="{{data.modules.ido2db.database.password}}" "{{data.modules.ido2db.database.name}}" < "{{tmpf}}"
    {% endif %}
    - watch:
      - file: icinga2-import-mysql-schema
    - watch_in:
      - mc_proxy: icinga2-pre-install

# check schema importation
# TODO

{% endif %}
{% endif %}
