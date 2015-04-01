{% set settings = salt['mc_slapd.settings']() %}
{% set yameld_data = salt['mc_utils.json_dump'](settings) %}
include:
  - makina-states.services.dns.slapd.hooks
  - makina-states.services.dns.slapd.tls-setup
  - makina-states.services.dns.slapd.generate-acl
  - makina-states.services.dns.slapd.cleanup-schema
  {% if grains['os'] in ['Ubuntu'] %}
  - makina-states.services.dns.slapd.fix-apparmor
  {% endif %}
  - makina-states.services.dns.slapd.services


slapd_usertosslcerts:
  user.present:
    - name: {{settings.user}}
    - remove_groups: False
    - system: true
    - optional_groups: [ssl-cert]
    - watch:
      - mc_proxy: slapd-post-install
    - watch_in:
      - mc_proxy: slapd-pre-conf

slapd_directory:
  file.directory:
    - name: {{ settings.slapd_directory }}
    - user: {{settings.user}}
    - group: {{settings.group}}
    - mode: 775
    - makedirs: True
    - watch:
      - mc_proxy: slapd-post-install
    - watch_in:
      - mc_proxy: slapd-pre-conf

{% for tp in [ '/etc/default/slapd', ] %}
slapd_config_{{tp}}:
  file.managed:
    - name: {{tp}}
    - makedirs: true
    - source: salt://makina-states/files{{tp}}
    - template: jinja
    - mode: 750
    - user: {{settings.user}}
    - group: {{settings.group}}
    - watch:
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf
{% endfor %}
{% for tp in settings.cn_config_files %}
slapd_config_{{tp}}:
  file.managed:
    - name: {{ tp }}
    - source: salt://makina-states/files{{tp}}
    - template: jinja
    - makedirs: true
    - mode: 640
    - user: {{settings.user}}
    - group: {{settings.group}}
    - watch:
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf
{% endfor %}
