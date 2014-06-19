{{ salt['mc_macros.register']('services', 'backup.dbsmartbackup') }}
include:
  - makina-states.services.backup.dbsmartbackup.prerequisites
  - makina-states.services.backup.dbsmartbackup.configuration
