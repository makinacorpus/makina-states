{% set settings = salt['mc_slapd.settings']() %}

include:
  - makina-states.localsettings.ssl.hooks

slapd-checkconf:
  cmd.run:
    - name: slaptest -v   -F "{{settings.SLAPD_CONF}}" -d 32768 -u
    - unless: slaptest -v -F "{{settings.SLAPD_CONF}}" -d 32768 -u
    {# do not trigger reload but report problems #}
    - user: root
    - watch:
      - mc_proxy: ssl-certs-post-hook
      - mc_proxy: slapd-pre-restart
    - watch_in:
      - mc_proxy: slapd-post-restart

slapd-service-restart:
  service.running:
    - name: {{settings.service_name}}
    - enable: True
    - watch:
      - mc_proxy: slapd-pre-restart
    - watch_in:
      - mc_proxy: slapd-post-restart
