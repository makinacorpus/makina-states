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
  - makina-states.services.db.mysql.services
  - makina-states.services.db.mysql.checkroot

{% import "makina-states/services/db/mysql/init.sls" as macros with context %}
{{macros.gen_settings()}}

{% for user, data in mysqlData.get('users', {}).items() %}
{% set data = data.copy() %}
{% set pw = data.pop('password', '') %}
{{macros.mysql_user(user, pw, **data) }}
{%endfor %}

# vim: set nofoldenable:
