{#
# - install a custom /etc/mysql/conf.d/local.cnf config script
# - reload salt modules to get the mysql salt modules available
# - ensure root password is set on servers
# - define the mysql restart/reload states, add watch_in on theses ones
#    * makina-mysql-service (restart)
#    * makina-mysql-service-reload (reload)
#}

{% set nodetypes_registry = salt['mc_nodetypes.registry']() %}
{%- set locs = salt['mc_locations.settings']() %}
{%- set mysqlSettings = salt['mc_mysql.settings']() %}

include:
  - makina-states.services.db.mysql.services
  - makina-states.services.db.mysql.checkroot

makina-mysql-settings:
  file.managed:
    - name: {{ mysqlSettings.etcdir }}/local.cnf
    - source: "{{ mysqlSettings.myCnf }}"
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - show_diff: True
    - defaults:
      data: |
            {{salt['mc_utils.json_dump'](mysqlSettings)}}
    - watch:
      - mc_proxy: mysql-pre-conf-hook
    - watch_in:
      - mc_proxy: mysql-post-conf-hook
# vim: set nofoldenable:
