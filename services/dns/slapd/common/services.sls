{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_slapd.settings']() %}
{% set yameld_data = salt['mc_utils.json_dump'](settings) %}

slapd-service-restart:
  service.running:
    - name: {{settings.service_name}}
    - enable: True
    - watch:
      - mc_proxy: slapd-pre-restart
    - watch_in:
      - mc_proxy: slapd-post-restart

slapd-service-reload:
  service.running:
    - name: {{settings.service_name}}
    - enable: True
    - reload: True
    - watch:
      - mc_proxy: slapd-pre-reload
    - watch_in:
      - mc_proxy: slapd-post-reload

{# switch back to our shiny new dns server #}
{{ switch_dns(suf='postslapdrestart',
              require_in=['mc_proxy: slapd-post-end'],
              require=['mc_proxy: slapd-post-restart'],
              dnsservers=['127.0.0.1']+settings.default_dnses) }}
{% endif %}
