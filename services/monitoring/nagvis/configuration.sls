{#-
# icinga
#
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_nagvis.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

include:
  - makina-states.services.monitoring.nagvis.hooks
  - makina-states.services.monitoring.nagvis.services


# general configuration
nagvis-conf:
  file.managed:
    - name: {{data.configuration_directory}}/nagvis.ini.php
    - source: salt://makina-states/files/etc/nagvis/nagvis.ini.php
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: nagvis-pre-conf
    - watch_in:
      - mc_proxy: nagvis-post-conf
    - defaults:
      data: |
            {{sdata}}

nagvis-global-conf:
  file.managed:
    - name: /usr/share/nagvis/share/server/core/defines/global.php
    - source: salt://makina-states/files/usr/share/nagvis/share/server/core/defines/global.php
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: nagvis-pre-conf
    - watch_in:
      - mc_proxy: nagvis-post-conf
    - defaults:
      data: |
            {{sdata}}

# configure the root account
{% set tmpf = '/tmp/root-account.sql' %}
nagvis-root-account:
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
                 "update users set name='{{data.root_account.user}}' where userId=1"
                 "update users set password='{{data.root_account.hashed_password}}' where userId=1"
                )
                res=0;
                if [ "$(sqlite3 "{{data.configuration_directory}}/auth.db" 'select password from users where userId=1;')" == "{{data.root_account.default_password}}" ]; then
                    for query in "${sql_queries[@]}"; do
                     sqlite3 "{{data.configuration_directory}}/auth.db" "$query;"
                     res_tmp=$?
                     if [ 0 -eq "$res" ]; then
                      res=$res_tmp
                     fi;
                    done;
                fi;
                rm "{{tmpf}}";
                exit "$res";

  cmd.run:
    - name: {{tmpf}}
    - watch:
      - mc_proxy: nagvis-pre-conf
      - file: nagvis-root-account
    - watch_in:
       - mc_proxy: nagvis-post-conf

# add geomap hosts
{% for name, geomap in data.geomap.items() %}
nagvis-geomap-{{name}}-conf:
  file.managed:
    - name: {{data.configuration_directory}}/geomap/{{name}}.csv
    - source: salt://makina-states/files/etc/nagvis/geomap/template.csv
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: nagvis-pre-conf
    - watch_in:
      - mc_proxy: nagvis-post-conf
    - defaults:
      data: |
            {{salt['mc_utils.json_dump'](geomap)}}

{% endfor %}


{%- import "makina-states/services/monitoring/icinga/macros.jinja" as icinga with context %}
{#
{{icinga.icingaAddWatcher('foo', '/bin/echo', args=[1]) }}
#}
