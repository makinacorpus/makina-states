{% import "makina-states/_macros/h.jinja" as h with context %}
{% import "makina-states/localsettings/ssl/macros.jinja" as ssl with context %}
{#
# - install a custom /etc/mysql/conf.d/local.cnf config script
# - reload salt modules to get the mysql salt modules available
# - ensure root password is set on servers
# - define the mysql restart/reload states, add watch_in on theses ones
#    * makina-mysql-service (restart)
#    * makina-mysql-service-reload (reload)
#}
{%- set mysqlData = salt['mc_mysql.settings']() %}
include:
  - makina-states.localsettings.ssl
  - makina-states.services.db.mysql.services
  - makina-states.services.db.mysql.checkroot

{% import "makina-states/services/db/mysql/init.sls" as macros with context %}

makina-mysql-settings-pre:
  file.absent:
    - names:
      - /etc/mysql/mysql.conf.d/mysqld_safe_syslog.cnf
      - /etc/mysql/mysql.conf.d/mysqld.cnf
    - watch:
      - mc_proxy: mysql-pre-conf-hook
    - watch_in:
      - mc_proxy: mysql-post-conf-hook

{% macro rmacro() %}
    - watch:
      - mc_proxy: mysql-pre-conf-hook
    - watch_in:
      - mc_proxy: mysql-post-conf-hook
{% endmacro %}
{{ h.deliver_config_files(
     mysqlData.get('configs', {}),
     mode='644',
     after_macro=rmacro, prefix='mysql-')}}

{% for user, data in mysqlData.get('users', {}).items() %}
{% set data = data.copy() %}
{% set pw = data.pop('password', '') %}
{{macros.mysql_user(user, pw, **data) }}
{%endfor %}

mysql-reload-systemd:
  cmd.watch:
    - name: "systemctl daemon-reload"
    - watch:
      - mc_proxy: mysql-post-conf-hook
      - file: mysql-/etc/systemd/system/overrides.d/mysql.conf
    - watch_in:
      - mc_proxy: mysql-pre-restart-hook

{% macro rsmacro() %}
    - watch:
      - mc_proxy: mysql-pre-conf-hook
    - watch_in:
      - mc_proxy: mysql-post-conf-hook
{% endmacro %}
{{ ssl.install_cert_in_dir(cert_infos=mysqlData.cert_infos,
                           user=mysqlData.user,
                           group=mysqlData.user,
                           suf='mysql')}}
# vim: set nofoldenable:
