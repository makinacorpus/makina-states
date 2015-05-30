{% set settings = salt['mc_slapd.settings']() %}
{% import "makina-states/_macros/h.jinja" as h with context %}
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

{% macro rmacro() %}
    - watch:
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf
{% endmacro %}
{{ h.deliver_config_files(
     settings.get('cn_config_files', {}), 
     user=settings.user,
     group=settings.group,
     mode='640',
     after_macro=rmacro, prefix='slapd-')}}
