{{ salt['mc_macros.register']('services', 'db.redis') }}
include:
  - makina-states.services.db.redis.prerequisites
  - makina-states.services.db.redis.configuration
  - makina-states.services.db.redis.services
  - makina-states.services.backup.dbsmartbackup

{# macro exports #}
{% import "makina-states/services/db/redis/macros.sls" as macros with context %}
{% set redis_db = macros.redis_db %}
{% set redis_user = macros.redis_user %}
