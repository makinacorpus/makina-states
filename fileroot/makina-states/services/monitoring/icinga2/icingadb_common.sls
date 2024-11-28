{% set locs = salt['mc_locations.settings']() %}
{% set icinga2Settings = salt['mc_icinga2.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](icinga2Settings) %}
include:
  - makina-states.services.monitoring.icinga2.hooks
icinga-check-pw:
  cmd.run:
    - name: test "x{{icinga2Settings.modules.icingadb.database.password}}" != "x"
    - require_in:
      - mc_proxy: icinga2-safe-checks
icinga2-db-pkgs:
  pkg.installed:
    - pkgs: {{icinga2Settings.modules.icingadb.package}}
    - watch_in:
      - mc_proxy: icingadb-presetup
{% for f in ['/etc/icingadb/config.yml'] %}
icinga2-db-file-{{f}}:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files/{{f}}
    - user: root
    - makedirs: true
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
      data: |
            {{sdata}}
    - watch:
      - mc_proxy: icingadb-presetup
    - watch_in:
      - mc_proxy: icingadb-postsetup
{% endfor %}
icinga2-db-start:
  {%set f = '/etc/systemd/system/icingadb.service.d/dropin.conf' %}
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files/{{f}}
    - user: root
    - makedirs: true
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
      data: |
            {{sdata}}
  service.running:
    - name: icingadb
    - enable: True
    - watch:
      - file: icinga2-db-start
      - mc_proxy: icingadb-postsetup
    - watch_in:
      - mc_proxy: icingadb-endsetup
