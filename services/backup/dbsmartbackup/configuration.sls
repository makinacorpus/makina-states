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
{% set data=salt['mc_dbsmartbackup.settings']() %}
{% set settings=salt['mc_utils.json_dump'](salt['mc_dbsmartbackup.settings']()) %}
run_dbsmartbackups:
  cron.absent: {# retro compat #}
    - identifier: db_smart_backup cron
    - name: {{locs.bin_dir}}/run_dbsmartbackups.sh
    - user: root
    - hour: {{data.cron_hour}}
    - minute: {{data.cron_minute}}


run_dbsmartbackups-cron:
{% if not data.cron_activated %}
  file.absent:
    - name: /etc/cron.d/run_dbsmartbackups
{% else %}
  file.managed:
    - name: /etc/cron.d/run_dbsmartbackups
    - source: ''
    - mode: 750
    - user: root
    - group: root
    - template: jinja
    - contents: |
                {{data.cron_minute}} {{data.cron_hour}} * * * root {{locs.apps_dir}}/db_smart_backup/run_dbsmartbackups.sh --quiet --no-colors
{% endif %}

dbsmartbackup_pg_conf:
  file.managed:
    - name: /etc/dbsmartbackup/postgresql.conf
    - source: salt://makina-states/files/etc/dbsmartbackup/postgresql.conf
    - makedirs: true
    - template: jinja
    - mode: 700

dbsmartbackup_mysql_conf:
  file.managed:
    - name: /etc/dbsmartbackup/mysql.conf
    - source: salt://makina-states/files/etc/dbsmartbackup/mysql.conf
    - makedirs: true
    - template: jinja
    - mode: 700

dbsmartbackup_mongodb.conf:
  file.managed:
    - name: /etc/dbsmartbackup/mongod.conf
    - source: salt://makina-states/files/etc/dbsmartbackup/mongod.conf
    - makedirs: true
    - template: jinja
    - mode: 700

dbsmartbackup_redis.conf:
  file.managed:
    - name: /etc/dbsmartbackup/redis.conf
    - source: salt://makina-states/files/etc/dbsmartbackup/redis.conf
    - makedirs: true
    - template: jinja
    - mode: 700

dbsmartbackup_slapd.conf:
  file.managed:
    - name: /etc/dbsmartbackup/slapd.conf
    - source: salt://makina-states/files/etc/dbsmartbackup/slapd.conf
    - makedirs: true
    - template: jinja
    - mode: 700

dbsmartbackup_elasticsearch_conf:
  file.managed:
    - name: /etc/dbsmartbackup/elasticsearch.conf
    - source: salt://makina-states/files/etc/dbsmartbackup/elasticsearch.conf
    - makedirs: true
    - template: jinja
    - mode: 700
