{{ salt['mc_macros.register']('services', 'db.mongodb') }}
include:
  - makina-states.services.db.mongodb.prerequisites
  - makina-states.services.db.mongodb.configuration
  - makina-states.services.db.mongodb.service
  - makina-states.services.db.mongodb.create-admin
  - makina-states.services.backup.dbsmartbackup
