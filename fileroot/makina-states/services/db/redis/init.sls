{{ salt['mc_macros.register']('services', 'db.redis') }}
include:
  - makina-states.services.db.redis.prerequisites
  - makina-states.services.db.redis.configuration
  - makina-states.services.db.redis.services
  - makina-states.services.backup.dbsmartbackup
