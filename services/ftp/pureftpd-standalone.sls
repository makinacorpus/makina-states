{#-
# Install in full mode, see the standalone file !
#}
{#-
# Pure FTPd service
# Read the pureftpd section of _macros/services.jinja to know which grain/pillar settings
# can modulate your pureftpd installation
#}
{%- import "makina-states/_macros/services.jinja" as services with context %}
{% macro do(full=True) %}
{{ salt['mc_macros.register']('services', 'ftp.pureftpd') }}
{%- set localsettings = services.localsettings %}
{%- set nodetypes = services.nodetypes %}
{%- set locs = localsettings.locations %}
{%- set key = locs.conf_dir+'/ssl/private/pure-ftpd.pem' %}
{%- set passive = services.pureftpdSettings['PassiveIP'] or services.pureftpdSettings['PassivePortRange']%}
{%- if grains['os_family'] in ['Debian'] %}
{% macro service_watch_in() %}
    - watch_in:
      - service: pure-ftpd-service
{% endmacro %}

{% if full %}
prereq-pureftpd:
  pkg.installed:
    {{ service_watch_in() }}
    - pkgs:
      {%- if services.pureftpdSettings.LDAPConfigFile %}
      - pure-ftpd-ldap
      {%- elif services.pureftpdSettings.MySQLConfigFile %}
      - pure-ftpd-mysql
      {%- elif services.pureftpdSettings.PGSQLConfigFile %}
      - pure-ftpd-postgresql
      {%- else %}
      - pure-ftpd
      {%- endif %}
{% endif %}

{{ locs.conf_dir }}/default/pure-ftpd-common-makina-pure-ftpd:
  file.managed:
    - name: {{ locs.conf_dir }}/default/pure-ftpd-common
    - source: salt://makina-states/files/etc/default/pure-ftpd-common
    - user: root
    - group: root
    - mode: 700
    - template: jinja
    - virtualchroot: '{{services.pureftpdDefaultSettings.Virtualchroot}}'
    - inetdMode: '{{services.pureftpdDefaultSettings.InetdMode}}'
    - uploadUid: '{{services.pureftpdDefaultSettings.UploadUid}}'
    - uploadGid: '{{services.pureftpdDefaultSettings.UploadGid}}'
    - uploadScript: '{{services.pureftpdDefaultSettings.UploadScript}}'

{%- for setting, value in services.pureftpdSettings.items() %}
{%- if (
    value.strip()
    and (
      not setting.startswith('Passive')
      or (setting.startswith('Passive') and passive)
    )
) %}
{{ locs.conf_dir }}/pure-ftpd/conf/{{setting}}-makina-pure-ftpd:
  file.managed:
    - name: {{ locs.conf_dir }}/pure-ftpd/conf/{{setting}}
    - user: root
    - group: root
    - mode: 700
    - contents: |
                {{value}}
    {{ service_watch_in() }}
{%- else %}
{{ locs.conf_dir }}/pure-ftpd/conf/{{setting}}-makina-pure-ftpd:
  file.absent:
    - name: {{ locs.conf_dir }}/pure-ftpd/conf/{{setting}}
    {{ service_watch_in() }}
{%- endif %}
{%- endfor %}

{%- set ssl = services.SSLSettings %}
{{key}}-makina-pureftpd:
  cmd.run:
    - name: |
            openssl req -batch -x509 -nodes -days 36500 -newkey rsa:2048 \
            -keyout "{{key}}" -out "{{key}}" \
            -subj "/C={{ssl.country}}/ST={{ssl.st}}/L={{ssl.l}}/O={{ssl.o}}/CN={{ssl.cn}}/EMAIL={{ssl.email}}"
    - unless: test -e {{key}}
    {{ service_watch_in() }}
      - cmd: {{key}}-makina-pureftpd-perm

{{key}}-makina-pureftpd-perm:
  cmd.script:
    - source: 'file://{{services.saltmac.msr}}/_scripts/reset-perms.sh'
    - template: jinja
    - msr: {{ services.saltmac.msr }}
    - dmode: 0700
    - fmode: 0700
    - user: root
    - group: root
    - reset_paths:
      - {{ key }}
    {{ service_watch_in() }}

makina-pureftpd-shell-contents:
  file.accumulated:
    - require_in:
      - file: makina-pureftpd-shell-block
    - filename: {{ locs.conf_dir }}/shells
    - text: /bin/ftponly

makina-pureftpd-shell-block:
  file.blockreplace:
    - name: {{ locs.conf_dir }}/shells
    - marker_start: "#-- start pureftpd salt managed zonestart -- PLEASE, DO NOT EDIT"
    - marker_end: "#-- end salt pureftpd managed zonestart --"
    - content: ''
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    {{ service_watch_in() }}

pure-ftpd-service:
  service.running:
    - name: pure-ftpd
{%- endif %}

{% endmacro %}
{{ do(full=False) }}
