{#-
# Integration of db_smart_backup to backup postgresql & mysql databases
# configured through makina-states
#
# The whole idea is not to try to install or deactivate a specific cron for
# each particular database server, but try to run on each version that we
# can detect
#
# For mysql, you certainly need the root password setting in yout pillar:
#  makina-states.services.db.mysql.root_passwd: <rootpw>
#}
{%- set locs = salt['mc_locations.settings']() %}
{{ salt['mc_macros.register']('services', 'backup.dbsmartbackup') }}
{% set data=salt['mc_dbsmartbackup.settings']() %}
{% set settings=salt['mc_utils.json_dump'](salt['mc_dbsmartbackup.settings']()) %}

db_smart_backup:
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

db_smart_backup-sym:
  file.symlink:
    - name: /usr/bin/db_smart_backup.sh
    - target: {{locs.apps_dir}}/db_smart_backup/db_smart_backup.sh
    - require:
      - mc_git: db_smart_backup

run_dbsmartbackups:
  file.managed:
    - name: {{locs.bin_dir}}/run_dbsmartbackups.sh
    - source: salt://makina-states/files/usr/bin/run_dbsmartbackups.sh
    - mode: 750
    - makedirs: true
    - user: root
    - group: root
    - template: jinja
    - context:
      settings: |
                {{settings}}
  cron.present:
    - identifier: db_smart_backup cron
    - name: {{locs.bin_dir}}/run_dbsmartbackups.sh
    - user: root
    - hour: {{data.cron_hour}}
    - minute: {{data.cron_minute}}

dbsmartbackup_pg_conf:
  file.managed:
    - name: /etc/dbsmartbackup/postgresql.conf
    - makedirs: true
    - source: salt://makina-states/files/etc/dbsmartbackup/postgresql.conf
    - template: jinja
    - mode: 700
    - context:
      settings: |
                {{settings}}

dbsmartbackup_mongod_conf:
  file.managed:
    - makedirs: true
    - name: /etc/dbsmartbackup/mongod.conf
    - source: salt://makina-states/files/etc/dbsmartbackup/mongod.conf
    - template: jinja
    - mode: 700
    - context:
      settings: |
                {{settings}}

dbsmartbackup_mysql_conf:
  file.managed:
    - makedirs: true
    - name: /etc/dbsmartbackup/mysql.conf
    - source: salt://makina-states/files/etc/dbsmartbackup/mysql.conf
    - template: jinja
    - mode: 700
    - context:
      settings: |
                {{settings}}

