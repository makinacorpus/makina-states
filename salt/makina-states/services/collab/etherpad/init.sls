{#-
# Etherpad server: https://github.com/ether/etherpad-lite
#}
{%- import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}

{{- salt['mc_macros.register']('services', 'collab.etherpad') }}
{%- set locs = salt['mc_locations.settings']() %}
{%- set etherpadSettings = salt['mc_etherpad.settings']() %}

{%- set etherpadLocation = etherpadSettings['location'] + "/etherpad-lite-" + etherpadSettings['version'] %}

include:
  - makina-states.localsettings.nodejs
  - makina-states.services.monitoring.circus

etherpad-create-user:
  user.present:
    - name: etherpad
    - shell: /bin/bash
    - gid_from_name: True
    - remove_groups: False
    - require:
        - pkg: nodejs-pkgs

{#- Download and install etherpad #}
etherpad-create-directory:
  file.directory:
    - name: {{ etherpadSettings['location'] }}
    - dir_mode: 755
    - makedirs: True

{%- endif %}
etherpad-install-pkg:
  file.directory:
    - name: {{ etherpadSettings['location'] }}
    - user: etherpad
    - group: etherpad
    - mode: 775
  archive.extracted:
    - name: {{ etherpadSettings['location'] }}
    - archive_format: zip
    - if_missing: {{ etherpadSettings['location']}}/etherpad-lite-{{etherpadSettings['version']}}/var
    - source: https://github.com/ether/etherpad-lite/archive/{{ etherpadSettings['version'] }}.zip
    - source_hash: md5=af569ee46c7e14c84002aa7a8d6d29bd
    - require_in:
      - pkg: etherpad-npms
      - cmd: etherpad-install-perms
    - require:
      - user: etherpad
      - file: etherpad-create-directory
etherpad-install-perms:
  file.managed:
    - name: {{etherpadLocation}}/reset-perms.sh
    - source:
    - user: root
    - group: root
    - mode: 755
    - contents: >
                #!/usr/bin/env bash

                {{locs.resetperms}}
                -u etherpad -g etherpad
                --path "{{etherpadLocation}}"
                --fmode 775 --dmode 775
                --groups {{salt['mc_usergroup.settings']().group}}
  cmd.run:
    - name: {{etherpadLocation}}/reset-perms.sh
    - require_in:
      - file: etherpad-apikey
      - file: etherpad-settings

{# Configuration -#}
etherpad-apikey:
  file.managed:
    - name: {{ etherpadLocation }}/APIKEY.txt
    - contents: {{ etherpadSettings['apikey'] }}
    - mode: 600
    - user: etherpad
    - group: etherpad
    - require_in:
      - file: circus-add-watcher-etherpad

etherpad-settings:
  file.managed:
    - name: {{ etherpadLocation }}/settings.json
    - source: salt://makina-states/files/home/etherpad/settings.json
    - template: jinja
    - mode: 600
    - defaults:
      data: |
            {{salt['mc_utils.json_dump']( etherpadSettings)}}
    - user: etherpad
    - group: etherpad
    - require_in:
      - file: circus-add-watcher-etherpad

etherpad-npms:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - sqlite3
      - libsqlite3-dev
  npm.installed:
    - names:
      - node-sqlite3
      - sqlite3
    - dir: {{etherpadLocation}}
    - require:
      - pkg: etherpad-npms
    - watch_in:
      - cmd: etherpad-install-perms

{#- Run #}
{{ circus.circusAddWatcher("etherpad",
                           etherpadLocation +"/bin/run.sh",
                           uid='etherpad',
                           gid='etherpad',
                           shell=True,
                           working_dir=etherpadLocation) }}

