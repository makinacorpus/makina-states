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
    - watch:
      - file: icinga2-import-pgsql-schema
      - mc_proxy: makina-postgresql-post-base
    - watch_in:
      - mc_proxy: icinga2-pre-install

# check schema importation
{% set tmpf = '/tmp/icinga2-ido.check.sql' %}
icinga2-check-pgsql-schema:
  file.managed:
    - name: {{tmpf}}
    - source: ''
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - contents: |
                #!/bin/bash
                sql_queries=(
                 "select 59=count(*) as ok from information_schema.tables where table_schema='public'"
                 "select 155=count(*) as ok from information_schema.table_constraints"
                 "select 209=count(*) as ok from pg_index as idx
                  join pg_class as i on i.oid = idx.indexrelid
                  join pg_namespace as ns on ns.oid = i.relnamespace and ns.nspname = any(current_schemas(false))"
                )
                for query in "${sql_queries[@]}"; do
                 {% if 'socket' in data.modules.ido2db.database %}
                  res="$(echo "select row_to_json(row) from ($query) row;" | psql -t "postgresql://{{data.modules.ido2db.database.user}}:{{data.modules.ido2db.database.password}}@[{{data.modules.ido2db.database.socket}}]/{{data.modules.ido2db.database.name}}" | jq .ok)"
                 {% else %}
                  res="$(echo "select row_to_json(row) from ($query) row;" | psql -t "postgresql://{{data.modules.ido2db.database.user}}:{{data.modules.ido2db.database.password}}@{{data.modules.ido2db.database.host}}:{{data.modules.ido2db.database.port}}/{{data.modules.ido2db.database.name}}" | jq .ok)"
                 {% endif %}
                 if [ "xtrue" != "x$res" ]; then
                  echo "Error with query \"$query;\"";
                  rm "{{tmpf}}";
                  exit 1;
                fi
                done;
                echo "OK";
                rm {{tmpf}};
                exit 0;

  cmd.run:
    - name: {{tmpf}}
    - watch:
       - cmd: icinga2-import-pgsql-schema
       - file: icinga2-check-pgsql-schema
    - watch_in:
       - mc_proxy: icinga2-pre-install

{% endif %}
{% endif %}
