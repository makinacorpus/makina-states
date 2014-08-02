{% set data=salt['mc_dbsmartbackup.settings']() %}
include:
  - makina-states.services.backup.dbsmartbackup.unregister
db_smart_backup-sym:
  file.absent:
    - names:
      - /usr/bin/db_smart_backup.sh
      - /etc/dbsmartbackup
      - /etc/cron.d/run_dbsmartbackups
