{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga_web2.settings']() %}

{% if 'pgsql' == data.databases.web.type %}
include:
  - makina-states.services.db.postgresql.hooks
  - makina-states.services.db.postgresql.client
  - makina-states.services.monitoring.icinga_web2.hooks

# import schema
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

{% set tmpf = '/usr/share/icingaweb2/etc/schema/pgsql.schema.sql' %}
icinga_web2-import-pgsql-schema:
  cmd.run:
    - name: psql "{{uri}}" -f "{{tmpf}}"
    - unless: echo "select * from icingaweb_user;" | psql "{{uri}}" --set ON_ERROR_STOP=1
    - watch:
      - mc_proxy: makina-postgresql-post-base
      - mc_proxy: icinga_web2-pre-install
    - watch_in:
      - mc_proxy: icinga_web2-post-install

{% for u, udata in data.users.items() %}
{% set pw = udata.password %}
{% set tmpf = '/tmp/icingaweb2user-{0}.sh'.format(u) %}
icinga_web-reset-{{u}}-do-pw:
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
                set -ex
                squery="select name from icingaweb_user where name = '{{udata.login}}'";
                sret=$(echo "$squery;" | psql --set ON_ERROR_STOP=1 -t "{{uri}}"|awk '{print $1}')
                if [ "x${sret}" = "x{{udata.login}}" ];then
                  query="UPDATE icingaweb_user SET active=1, password_hash='{{udata.password_hash}}' WHERE name='{{udata.login}}'"
                else
                  query="INSERT INTO icingaweb_user (name, active, password_hash) VALUES ('{{u}}', 1, '{{udata.password_hash}}')"
                fi
                echo "$query;" | psql --set ON_ERROR_STOP=1 -t "{{uri}}"
                res=${?}
                echo "changed=false"
                rm -f {{tmpf}};
                exit $res
    - require:
      - cmd: icinga_web2-import-pgsql-schema
    - require_in:
      - mc_proxy: icinga_web2-post-install
  cmd.run:
    - name: {{tmpf}}
    - stateful: true
    - require:
      - file: icinga_web-reset-{{u}}-do-pw
    - watch_in:
      - mc_proxy: icinga_web2-post-install
{% endfor %}
{% endif %}
