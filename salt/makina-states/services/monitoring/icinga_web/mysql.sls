{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga_web.settings']() %}

{% if 'mysql' == data.databases.web.type %}

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
icinga_web-create-mysql-user:
  mysql_database.present:
    - name: {{data.databases.web.user}}

# create database
{{ mysql_db(
    db=data.databases.web.name,
    user=data.databases.web.user,
    password=data.databases.web.password) }}

# import schema
{% set tmpf = '/tmp/icinga-web.schema.sql' %}
icinga_web-import-mysql-schema:
  file.managed:
    - name: {{tmpf}}
    - source: salt://makina-states/files/etc/icinga-web/schemas/icinga-web.mysql-schema.sql
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
  cmd.run:
    {% if 'socket' in data.databases.web %}
  - name: mysql --socket="{{data.databases.web.socket}}" --user="{{data.databases.web.user}}" --password="{{data.databases.web.password}}" "{{data.modules.databases.web.name}}" < "{{tmpf}}"
    {% else %}
    - name: mysql --host="{{data.databases.web.host}}" --port="{{data.databases.web.port}}" --user="{{data.databases.web.user}}" --password="{{data.databases.web.password}}" "{{data.databases.web.name}}" < "{{tmpf}}"
    {% endif %}
    - watch:
      - file: icinga_web-import-mysql-schema
    - watch_in:
      - mc_proxy: icinga_web-pre-install

# check schema importation
# TODO
{% endif %}
