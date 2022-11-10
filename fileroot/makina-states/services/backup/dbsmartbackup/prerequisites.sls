{%- set locs = salt['mc_locations.settings']() %}
{% set data=salt['mc_dbsmartbackup.settings']() %}
{% set settings=salt['mc_utils.json_dump'](salt['mc_dbsmartbackup.settings']()) %}

db_smart_backup:
  pkg.installed:
    - name: jq
  file.directory:
    - name: {{locs.apps_dir}}/db_smart_backup
    - user: root
    - mode: 700
    - makedirs: true
  mc_git.latest:
    - require:
      - file: db_smart_backup
    - name: https://github.com/kiorky/db_smart_backup.git
    - target: {{locs.apps_dir}}/db_smart_backup
    - user: root
    - force_reset: true

db_smart_backup-sym:
  file.symlink:
    - name: /usr/bin/db_smart_backup.sh
    - target: {{locs.apps_dir}}/db_smart_backup/db_smart_backup.sh
    - require:
      - mc_git: db_smart_backup

