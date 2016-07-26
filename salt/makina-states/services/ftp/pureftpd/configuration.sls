{% import "makina-states/_macros/h.jinja" as h with context %}
{#-
# Pure FTPd service
#}
include:
  - makina-states.services.ftp.pureftpd.hooks
  - makina-states.services.ftp.pureftpd.services

{% set settings = salt['mc_pureftpd.settings']() %}
{% set pureftpdSettings = settings.conf %}
{% set pureftpdDefaultSettings = settings.defaults %}
{%- set locs = salt['mc_locations.settings']() %}
{%- set key = locs.conf_dir+'/ssl/private/pure-ftpd.pem' %}
{%- set passive = pureftpdSettings['PassiveIP'] or pureftpdSettings['PassivePortRange']%}
{%- if grains['os_family'] in ['Debian'] %}
{% macro service_watch_in() %}
      - service: pure-ftpd-service
{% endmacro %}

{{ locs.conf_dir }}/pure-ftpd/auth/50puredb:
  file.symlink:
    - target: "/etc/pure-ftpd/conf/PureDB"
    - makedirs: true
    - watch:
      - mc_proxy: ftpd-pre-configuration-hook
    - watch_in:
      - mc_proxy: ftpd-post-configuration-hook

{{ locs.conf_dir }}/default/pure-ftpd-common-makina-pure-ftpd:
  file.managed:
    - name: {{ locs.conf_dir }}/default/pure-ftpd-common
    - source: salt://makina-states/files/etc/default/pure-ftpd-common
    - user: root
    - group: root
    - mode: 700
    - template: jinja
    - virtualchroot: '{{pureftpdDefaultSettings.Virtualchroot}}'
    - inetdMode: '{{pureftpdDefaultSettings.InetdMode}}'
    - uploadUid: '{{pureftpdDefaultSettings.UploadUid}}'
    - uploadGid: '{{pureftpdDefaultSettings.UploadGid}}'
    - uploadScript: '{{pureftpdDefaultSettings.UploadScript}}'
    - watch:
      - mc_proxy: ftpd-pre-configuration-hook
    - watch_in:
      - mc_proxy: ftpd-post-configuration-hook

{%- for setting, value in pureftpdSettings.items() %}
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
    - watch:
      - mc_proxy: ftpd-pre-configuration-hook
    - watch_in:
      - mc_proxy: ftpd-post-configuration-hook
{%- else %}
{{ locs.conf_dir }}/pure-ftpd/conf/{{setting}}-makina-pure-ftpd:
  file.absent:
    - name: {{ locs.conf_dir }}/pure-ftpd/conf/{{setting}}
    - watch:
      - mc_proxy: ftpd-pre-configuration-hook
    - watch_in:
      - mc_proxy: ftpd-post-configuration-hook
{%- endif %}
{%- endfor %}

{%- set ssl = salt['mc_ssl.settings']() %}
{%- set ca = ssl.ca %}
{{key}}-makina-pureftpd:
  cmd.run:
    - name: |
            openssl req -batch -x509 -nodes -days 36500 -newkey rsa:2048 \
             -keyout "{{key}}" -out "{{key}}" \
             -subj "/C={{ca.C}}/ST={{ca.ST}}/L={{ca.L}}/O={{ca.O}}/CN={{ca.CN}}/EMAIL={{ca.emailAddress}}"
    - unless: test -e {{key}}
    - watch:
      - mc_proxy: ftpd-pre-configuration-hook
    - watch_in:
      - mc_proxy: ftpd-post-configuration-hook
      - cmd: {{key}}-makina-pureftpd-perm

{{key}}-makina-pureftpd-perm:
  cmd.run:
    - name: >
            '{{salt['mc_salt.settings']()['msr']}}/_scripts/reset-perms.py'
            --dmode 0700 --fmode 0700 --no-acls
            --user root --group root
            --paths {{ key }}
    - watch:
      - mc_proxy: ftpd-pre-configuration-hook
    - watch_in:
      - mc_proxy: ftpd-post-configuration-hook

{% macro rmacro() %}
    - watch:
      - mc_proxy: ftpd-pre-configuration-hook
    - watch_in:
      - mc_proxy: ftpd-post-configuration-hook
{% endmacro %}
{{ h.deliver_config_files(settings.defaults.configs, after_macro=rmacro, prefix='pureftp-conf-')}}

makina-pureftpd-shell-contents:
  file.accumulated:
    - require_in:
      - file: makina-pureftpd-shell-block
    - filename: {{ locs.conf_dir }}/shells
    - text: /bin/ftponly
    - watch:
      - mc_proxy: ftpd-pre-configuration-hook
    - watch_in:
      - mc_proxy: ftpd-post-configuration-hook
      - cmd: {{key}}-makina-pureftpd-perm

makina-pureftpd-shell-block:
  file.blockreplace:
    - name: {{ locs.conf_dir }}/shells
    - marker_start: "#-- start pureftpd salt managed zonestart -- PLEASE, DO NOT EDIT"
    - marker_end: "#-- end salt pureftpd managed zonestart --"
    - content: ''
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - watch:
      - mc_proxy: ftpd-pre-configuration-hook
    - watch_in:
      - mc_proxy: ftpd-post-configuration-hook

{% endif %}
makina-pureftpd-mkdb:
  file.managed:
    - name: {{ locs.conf_dir }}/pure-ftpd/pureftpd.passwd
    - source: ''
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: ftpd-post-configuration-hook
    - watch_in:
      - mc_proxy: ftpd-pre-restart-hook
  cmd.run:
    - name: pure-pw mkdb
    - watch:
      - file: makina-pureftpd-mkdb
      - mc_proxy: ftpd-post-configuration-hook
    - watch_in:
      - mc_proxy: ftpd-pre-restart-hook

