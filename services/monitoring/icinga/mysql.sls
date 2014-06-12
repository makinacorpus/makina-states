{% set data = salt['mc_icinga.settings']() %}
{% set locs = salt['mc_locations.settings']() %}

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

# add the user
icinga-mysql:
  mysql_database.present:
    - name: icinga


# create the database
{{ mysql_db(
    db=data.modules.ido2db.database.name,
    user=data.modules.ido2db.database.user,
    password=data.modules.ido2db.database.password) }}

# import schema
# mysql.query supports only select statement
# this state is inspired by "services/db/postgresql/fix-template-1-encoding.sls"
{% set tmpf = '/tmp/icinga-ido.schema.sql' %}
import-mysql-schema:
  file.managed:
    - name: {{tmpf}}
    - source: salt://makina-states/files/etc/icinga/schemas/icinga-ido.mysql-schema.sql
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
  cmd.run:
    {% if 'socket' in data.modules.ido2db.database %}
  - name: mysql --socket="{{data.modules.ido2db.database.socket}}" --user="{{data.modules.ido2db.database.user}}" --password="{{data.modules.ido2db.database.password}}" "{{data.modules.ido2db.database.name}}" < "{{tmpf}}"
    {% else %}
    - name: mysql --host="{{data.modules.ido2db.database.host}}" --port="{{data.modules.ido2db.database.port}}" --user="{{data.modules.ido2db.database.user}}" --password="{{data.modules.ido2db.database.password}}" "{{data.modules.ido2db.database.name}}" < "{{tmpf}}"
    {% endif %}
    - watch:
      - file: import-mysql-schema
#      - mc_proxy: makina-mysql-post-base
    - watch_in:
      - mc_proxy: icinga-pre-install

# check schema importation
# TODO
{% endif %}
{% endif %}

