{% import "makina-states/_macros/services.jinja" as services with context %}
include:
  - makina-states.services.cloud.lxc.hooks
{% if services.lxcSettings['cron_sync'] %}
syncron-lxc-ms:
  cron.present:
    - minute: {{services.lxcSettings.cron_minute}}
    - hour: {{services.lxcSettings.cron_hour}}
    - name: /usr/bin/mastersalt-run -linfo mc_lxc.sync_images > /dev/null
    - identifier: ms lxc image synchronniser
    - watch_in:
      - mc_proxy: salt-cloud-lxc-default-template
{% endif %}
