{% set rsyslogSettings = salt['mc_rsyslog.settings']() %}
include:
  - makina-states.services.log.rsyslog.hooks
rsyslog-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - rsyslog
    - watch:
      - mc_proxy: rsyslog-pre-install-hook
    - watch_in:
      - mc_proxy: rsyslog-pre-hardrestart-hook
      - mc_proxy: rsyslog-post-install-hook
