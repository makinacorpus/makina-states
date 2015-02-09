{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga_web.settings']() %}

{% if 'pgsql' == data.databases.web.type %}

{% import "makina-states/services/db/postgresql/init.sls" as pgsql with context %}

include:

  # install postgresql
  {% if data.has_pgsql and data.create_pgsql %}
  - makina-states.services.db.postgresql
  {% else %}
  - makina-states.services.db.postgresql.hooks
  {% endif %}

icinga2-web-cli-pkgs:
  pkg.installed:
    - pkgs: [postgresql-client]
    - watch:
      - mc_proxy: makina-postgresql-post-base
    - watch_in:
       - mc_proxy: icinga_web-pre-install

{% if data.create_pgsql %}
# create database
{{ pgsql.postgresql_db(db=data.databases.web.name) }}

# add user
{{ pgsql.postgresql_user(name=data.databases.web.user,
                         password=data.databases.web.password,
                         db=data.databases.web.name) }}

{% endif %}

# import schema
{% set tmpf = '/tmp/icinga-web.schema.sql' %}
{% if 'socket' in data.databases.web %}
{% set uri = "postgresql://{0}:{1}@[{2}]/{3}".format(
  data.databases.web.user,
  data.databases.web.password,
  data.databases.web.socket,
  data.databases.web.name) %}
{% else %}
{% set uri = "postgresql://{0}:{1}@{2}:{3}/{4}".format(
  data.databases.web.user,
  data.databases.web.password,
  data.databases.web.host,
  data.databases.web.port,
  data.databases.web.name) %}
{% endif %}
icinga_web-import-pgsql-schema:
  file.managed:
    - name: {{tmpf}}
    - source: salt://makina-states/files/etc/icinga-web/schemas/icinga-web.pgsql-schema.sql
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
  cmd.run:
    - name: psql "{{uri}}" -f "{{tmpf}}"
    - unless: echo "select * from nsm_log;" | psql "{{uri}}" --set ON_ERROR_STOP=1
    - watch:
      - pkg: icinga2-web-cli-pkgs
      - file: icinga_web-import-pgsql-schema
      - mc_proxy: makina-postgresql-post-base
    - watch_in:
      - mc_proxy: icinga_web-pre-install

# update root password
{% set tmpf = '/tmp/icinga-web.password.sql' %}
icinga_web-reset-root-pw:
  file.managed:
    - name: {{tmpf}}
    - source: ''
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - unless: |
              if [ x" {{data.root_account.hashed_password}}{{data.root_account.salt}}" = x"$(echo "select user_password||user_salt from nsm_user where user_name='{{data.root_account.login}}'"|psql "{{uri}}" -t)" ];then
                exit 0
              fi
              exit 1
    - contents: |
                #!/bin/bash
                query="update nsm_user set user_password='{{data.root_account.hashed_password}}', user_salt='{{data.root_account.salt}}' where user_name='{{data.root_account.login}}'"
                echo "$query;" | psql --set ON_ERROR_STOP=1 -t "{{uri}}"
                res=${?}
                rm -f {{tmpf}};
                exit $res
  cmd.run:
    - unless: |
              if [ x" {{data.root_account.hashed_password}}{{data.root_account.salt}}" = x"$(echo "select user_password||user_salt from nsm_user where user_name='{{data.root_account.login}}'"|psql "{{uri}}" -t)" ];then
                exit 0
              fi
              exit 1
    - name: {{tmpf}}
    - watch:
      - pkg: icinga2-web-cli-pkgs
      - cmd: icinga_web-import-pgsql-schema
      - file: icinga_web-reset-root-pw
    - watch_in:
      - mc_proxy: icinga_web-pre-install


# delete logs in the database
# TODO: it is not a good idea but doctrine compilation reset serial when
# configuration change that produces "duplicate primary key in nsm_log"
{% set tmpf = '/tmp/icinga-web.clearlogs.sql' %}
icinga_web-clear-dblogs:
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
                sql_queries=('delete from nsm_log')
                for query in "${sql_queries[@]}"; do
                  res="$(echo "$query;" | psql -t "{{uri}}")"
                done;
                rm {{tmpf}};
                echo "changed=false"
                exit 0;
  cmd.run:
    - name: {{tmpf}}
#    - stateful: true
    - watch:
      - pkg: icinga2-web-cli-pkgs
      - cmd: icinga_web-import-pgsql-schema
      - file: icinga_web-clear-dblogs
    - watch_in:
      - mc_proxy: icinga_web-pre-install
{% endif %}
