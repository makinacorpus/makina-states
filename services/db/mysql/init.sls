{{ salt['mc_macros.register']('services', 'db.mysql') }}
include:
  - makina-states.services.db.mysql.prerequisites
  - makina-states.services.db.mysql.configuration
  - makina-states.services.db.mysql.services
  - makina-states.services.backup.dbsmartbackup

{# macro exports #}
{% import "makina-states/services/db/mysql/macros.sls" as macros with context %}
{% set gen_settings = macros.gen_settings %}
{% set mysql_db = macros.mysql_db %}
{% set mysql_user = macros.mysql_user %}
