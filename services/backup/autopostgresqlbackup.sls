{%- import "makina-states/_macros/services.jinja" as services with context %}
{%- set services = services %}
{%- set localsettings = services.localsettings %}
{%- set nodetypes = services.nodetypes %}
{%- set locs = localsettings.locations %}
{{- services.register('backup.autopostgresqlbackup') }}
{%- set default_user = services.postgresqlUser %}
autopostgresqlbackup:
  file.managed:
    - name: /usr/bin/autopostgresqlbackup.sh
    - source: salt://makina-states/files/usr/bin/autopostgresqlbackup.sh
    - user: root
    - mode: 755
    - template: jinja
    - context: {{services.autopostgresqlbackupSettings|yaml}}

autopostgresqlbackup-globals:
  file.managed:
    - name: /usr/bin/autopostgresqlbackup-globals.sh
    - source: salt://makina-states/files/usr/bin/autopostgresqlbackup.sh
    - user: root
    - mode: 755
    - template: jinja
    - context: {{services.autopostgresqlbackupGlobalSettings|yaml}}

autopostgresqlbackups:
  file.managed:
    - name: /usr/bin/autopostgresqlbackups.sh
    - source: salt://makina-states/files/usr/bin/autopostgresqlbackups.sh
    - user: root
    - mode: 755
    - context: {{services.autopostgresqlbackupSettings|yaml}}
