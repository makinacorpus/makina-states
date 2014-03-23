include:
  - makina-states.services.cloud.lxc.hooks
{% set settings = salt['mc_cloud_images.settings']() %}
{% if settings.lxc.cron_sync %}
syncron-lxc-ms:
  cron.present:
    - minute: {{settings.lxc.cron_minute}}
    - hour: {{settings.lxc.cron_hour}}
    - name: /usr/bin/mastersalt-run -linfo mc_lxc.sync_images > /dev/null
    - identifier: ms lxc image synchronniser
    - watch_in:
      - mc_proxy: salt-cloud-lxc-default-template
{% endif %}
