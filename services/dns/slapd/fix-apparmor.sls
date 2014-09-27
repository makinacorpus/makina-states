{% set settings = salt['mc_slapd.settings']() %}
{% set yameld_data = salt['mc_utils.json_dump'](settings) %}
include:
  - makina-states.services.dns.slapd.hooks
{% if grains['os'] in ['Ubuntu'] %}
{% if salt['mc_controllers.mastersalt_mode']() %}
{% set tp = '/etc/apparmor.d/usr.sbin.slapd' %}
slapd_config_apparmor:
  file.managed:
    - name: {{ tp }}
    - source: salt://makina-states/files{{tp}}
    - template: jinja
    - makedirs: true
    - mode: 640
    - user: {{settings.user}}
    - group: {{settings.group}}
    - defaults:
      data: |
            {{yameld_data}}
    - watch:
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf
      - service: apparmor-slapd-service-reload
apparmor-slapd-service-reload:
  cmd.wait:
    - name: service apparmor restart
    - watch:
      - file: slapd_config_apparmor
    - watch_in:
      - mc_proxy: slapd-post-conf
{% endif %}
{% endif %}
