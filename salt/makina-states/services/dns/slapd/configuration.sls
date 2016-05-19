{% set settings = salt['mc_slapd.settings']() %}
{% import "makina-states/_macros/h.jinja" as h with context %}
{% import "makina-states/localsettings/ssl/macros.jinja" as ssl with context %}
include:
  - makina-states.services.dns.slapd.hooks
  - makina-states.services.dns.slapd.tls-setup
  - makina-states.services.dns.slapd.generate-acl
  - makina-states.services.dns.slapd.cleanup-schema
  {% if grains['os'] in ['Ubuntu'] %}
  - makina-states.services.dns.slapd.fix-apparmor
  {% endif %}
  - makina-states.services.dns.slapd.services

{% macro rsmacro() %}
    - watch:
      - mc_proxy: slapd-post-install
    - watch_in:
      - mc_proxy: slapd-pre-conf
{% endmacro %}
{{ ssl.add_to_sslcerts(settings.user, rmacro=rsmacro, suf='ldap') }}

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
      - mc_proxy: slapd_directory-schema-pre
{% endmacro %}
{{ h.deliver_config_files(
     settings.get('cn_config_files', {}),
     user=settings.user,
     group=settings.group,
     mode='640',
     after_macro=rmacro, prefix='slapd-')}}
slapd_directory-schema-pre:
  mc_proxy.hook:
    - watch:
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf

{% if settings.fd_schema %}
slapd_directory-schema:
  file.recurse:
    - name: "/etc/ldap/slapd.d/cn=config/cn=schema"
    - source: "salt://makina-states/files/etc/ldap/slapd.d/cn=config/cn=schema/{{settings.fd_ver}}"
    - user: {{settings.user}}
    - group: {{settings.group}}
    - dir_mode: '0775'
    - file_mode: '0644'
    - template: false
    - makedirs: True
    - clean: true
    - watch:
      - mc_proxy: slapd_directory-schema-pre
      - mc_proxy: slapd-pre-conf
    - watch_in:
      - mc_proxy: slapd-post-conf
{% endif%}
