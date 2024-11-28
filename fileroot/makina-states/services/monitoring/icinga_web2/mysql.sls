{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga_web2.settings']() %}

{% if 'mysql' == data.databases.web.type %}
include:
  - makina-states.services.db.mysql.hooks
  - makina-states.services.db.mysql.client
  - makina-states.services.monitoring.icinga_web2.hooks

# import schema
{% set uri = "--user='{0}' --password='{1}' --host='{2}' --port='{3}' {4}".format(
  data.databases.web.user,
  data.databases.web.password,
  data.databases.web.host,
  data.databases.web.port,
  data.databases.web.name) %}

{% set tmpf = '/usr/share/icingaweb2/schema/mysql.schema.sql' %}
icinga_web2-import-mysql-schema:
  cmd.run:
    - name: mysql {{uri}} <"{{tmpf}}"
    - unless: echo "select * from icingaweb_user;" | mysql {{uri}}
    - watch:
      - mc_proxy: mysql-setup-access
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
                sret=$(echo "$squery;" | mysql -N -B {{uri}}|awk '{print $1}')
                if [ "x${sret}" = "x{{udata.login}}" ];then
                  query="UPDATE icingaweb_user SET active=1, password_hash='{{udata.password_hash}}' WHERE name='{{udata.login}}'"
                else
                  query="INSERT INTO icingaweb_user (name, active, password_hash) VALUES ('{{u}}', 1, '{{udata.password_hash}}')"
                fi
                echo "$query;" | mysql -N -b {{uri}}
                res=${?}
                echo "changed=false"
                rm -f {{tmpf}};
                exit $res
    - require:
      - cmd: icinga_web2-import-mysql-schema
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
