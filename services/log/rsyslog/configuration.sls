{% set data = salt['mc_rsyslog.settings']() %}
include:
  - makina-states.services.log.rsyslog.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
  - makina-states.services.log.rsyslog.services

makina-rsyslog-configuration-check:
  cmd.run:
    - name: rsyslogd -N1 && echo "changed=no"
    - stateful: true
    - watch:
      - mc_proxy: rsyslog-post-conf-hook
    - watch_in:
      - mc_proxy: rsyslog-pre-restart-hook

{% set sdata =salt['mc_utils.json_dump'](data) %}
{% for f in [
  '/etc/rsyslog.conf',
  '/etc/rsyslog.d/20-ufw.conf',
  '/etc/rsyslog.d/49-udp.conf',
  '/etc/rsyslog.d/50-default.conf',
  '/etc/rsyslog.d/haproxy.conf',
  '/etc/rsyslog.d/postfix.conf',
] %}
makina-rsyslog-{{f}}:
  file.managed:
    - name: {{f}}
    - makedirs: true
    - source: salt://makina-states/files/{{f}}
    - user: root
    - group: root
    - mode: 755
    - template: jinja
    - defaults:
      data: |
            {{sdata}}
    - watch:
      - mc_proxy: rsyslog-pre-conf-hook
    - watch_in:
      - mc_proxy: rsyslog-post-conf-hook
{% endfor %}

rsyslog-spool:
  file.directory:
    - name: {{data.spool}}
    - user: {{data.user}}
    - group: {{data.group}}
    - mode:  755
{%endif %}
