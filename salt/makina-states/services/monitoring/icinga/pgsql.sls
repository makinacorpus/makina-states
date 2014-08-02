{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

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

# create database
{{ pgsql.postgresql_db(db=data.modules.ido2db.database.name) }}

# add user
{{ pgsql.postgresql_user(name=data.modules.ido2db.database.user,
                         password=data.modules.ido2db.database.password,
                         db=data.modules.ido2db.database.name) }}


# import schema
{% set tmpf = '/tmp/icinga-ido.schema.sql' %}
icinga-import-pgsql-schema:
  file.managed:
    - name: {{tmpf}}
    - source: salt://makina-states/files/etc/icinga/schemas/icinga-ido.pgsql-schema.sql
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
      - file: icinga-import-pgsql-schema
      - mc_proxy: makina-postgresql-post-base
    - watch_in:
      - mc_proxy: icinga-pre-install

# check schema importation
{% set tmpf = '/tmp/icinga-ido.check.sql' %}
icinga-check-pgsql-schema:
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
                 "select 57=count(*) as ok from information_schema.tables where table_schema='public'"
                 "select 149=count(*) as ok from information_schema.table_constraints"
                 "select 204=count(*) as ok from pg_index as idx
                  join pg_class as i on i.oid = idx.indexrelid
                  join pg_namespace as ns on ns.oid = i.relnamespace and ns.nspname = any(current_schemas(false))"
                )
                for query in "${sql_queries[@]}"; do
                 {% if 'socket' in data.modules.ido2db.database %}
                  res="$(echo "select row_to_json(row) from ($query) row;" | psql -t "postgresql://{{data.modules.ido2db.database.user}}:{{data.modules.ido2db.database.password}}@[{{data.modules.ido2db.database.socket}}]/{{data.modules.ido2db.database.name}}" | jq .ok)"
                 {% else %}
                  res="$(echo "select row_to_json(row) from ($query) row;" | psql -t "postgresql://{{data.modules.ido2db.database.user}}:{{data.modules.ido2db.database.password}}@{{data.modules.ido2db.database.host}}:{{data.modules.ido2db.database.port}}/{{data.modules.ido2db.database.name}}" | jq .ok)"
                 {% endif %}
                 if [ "true" != "$res" ]; then
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
       - cmd: icinga-import-pgsql-schema
       - file: icinga-check-pgsql-schema
    - watch_in:
       - mc_proxy: icinga-pre-install

{% endif %}
{% endif %}
