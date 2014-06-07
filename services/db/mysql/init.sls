{{ salt['mc_macros.register']('services', 'db.mysql') }}
include:
  - makina-states.services.db.mysql.prerequisites
  - makina-states.services.db.mysql.configuration
  - makina-states.services.db.mysql.services
  - makina-states.services.backup.dbsmartbackup
