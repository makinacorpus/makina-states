{% import "makina-states/_macros/h.jinja" as h with context %}
{% set data = salt['mc_rsyslog.settings']() %}
include:
  - makina-states.services.log.rsyslog.hooks
  - makina-states.services.log.rsyslog.services

makina-rsyslog-configuration-check:
  cmd.run:
    - name: rsyslogd -N1 && echo "changed=no"
    - stateful: true
    - watch:
      - mc_proxy: rsyslog-post-conf-hook
    - watch_in:
      - mc_proxy: rsyslog-pre-restart-hook

{% macro rmacro() %}
    - watch:
      - mc_proxy: rsyslog-pre-conf-hook
    - watch_in:
      - mc_proxy: rsyslog-post-conf-hook
{% endmacro %}
{{ h.deliver_config_files(data.configs, mode='0755', after_macro=rmacro, prefix='rsyslogd-')}}

rsyslog-spool:
  file.directory:
    - name: {{data.spool}}
    - user: {{data.user}}
    - group: {{data.group}}
    - mode:  755
