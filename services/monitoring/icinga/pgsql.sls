{% set data = salt['mc_icinga.settings']() %}
{% set locs = salt['mc_locations.settings']() %}

{% if data.modules.ido2db.enabled %}
{% if 'pgsql' == data.modules.ido2db.database.type %}

{% import "makina-states/services/db/postgresql/init.sls" as pgsql with context %}

include:
  # if ido2db is enabled, install and configure the sgbd

  # install postgresql
  {% if data.has_pgsql %}
  - makina-states.services.db.postgresql
  {% else %}
  - makina-states.services.db.postgresql.hooks
  {% endif %}

# add the user
{{ pgsql.postgresql_user(data.modules.ido2db.database.user,
                         data.modules.ido2db.database.password)}}

# create the database
{{ pgsql.postgresql_db(data.modules.ido2db.database.name) }}

# import schema
# postgres.psql_query supports only select statement
# this state is inspired by "services/db/postgresql/fix-template-1-encoding.sls"
{% set tmpf = '/tmp/icinga-ido.schema.sql' %}
import-pgsql-schema:
  file.managed:
    - name: {{tmpf}}
    - source: salt://makina-states/files/etc/icinga/schemas/icinga-ido.schema.sql
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
  cmd.run:
    {% if 'socket' in data.modules.ido2db.database %}
    - name: psql "postgresql://{{data.modules.ido2db.database.user}}:{{data.modules.ido2db.database.password}}@[{{data.modules.ido2db.database.socket}}]/{{data.modules.ido2db.database.name}}" -f "{{tmpf}}"
    {% else %}
    - name: psql "postgresql://{{data.modules.ido2db.database.user}}:{{data.modules.ido2db.database.password}}@[{{data.modules.ido2db.database.host}}]:{{data.modules.ido2db.database.port}}/{{data.modules.ido2db.database.name}}" -f "{{tmpf}}"
    {% endif %}
    - watch:
      - mc_proxy: makina-postgresql-post-base
    - watch_in:
      - mc_proxy: icinga-pre-install
{% endif %}
{% endif %}

