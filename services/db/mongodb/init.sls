{{ salt['mc_macros.register']('services', 'db.mongodb') }}
include:
  - makina-states.services.db.mongodb.prerequisites
  - makina-states.services.db.mongodb.configuration
  - makina-states.services.db.mongodb.services
  - makina-states.services.db.mongodb.create-admin
  - makina-states.services.backup.dbsmartbackup

{# macro exports #}
{% import "makina-states/services/db/mongodb/macros.sls" as macros with context %}
{% set mongodb_db = macros.mongodb_db %}
{% set mongodb_user = macros.mongodb_user %}
