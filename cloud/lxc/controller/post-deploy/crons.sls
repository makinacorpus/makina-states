include:
  - makina-states.cloud.generic.hooks.controller
{% set settings = salt['mc_cloud_images.settings']() %}
{% if settings.lxc.cron_sync %}
syncron-lxc-ms:
  cron.present:
    - minute: {{settings.lxc.cron_minute}}
    - hour: {{settings.lxc.cron_hour}}
    - name: /usr/bin/mastersalt-run -linfo mc_lxc.sync_images > /dev/null
    - identifier: ms lxc image synchronniser
    - watch:
      - mc_proxy: cloud-generic-controller-pre-post-deploy
    - watch_in:
      - mc_proxy: cloud-generic-controller-post-post-deploy
{% endif %}
