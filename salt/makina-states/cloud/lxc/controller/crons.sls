{% set settings = salt['mc_cloud_images.settings']() %}
{% if settings.lxc.cron_sync %}
remove-syncron-lxc-ms:
  cron.absent:
    - minute: {{settings.lxc.cron_minute}}
    - hour: {{settings.lxc.cron_hour}}
    - name: /usr/bin/mastersalt-run -linfo mc_lxc.sync_images > /dev/null
    - identifier: ms lxc image synchronniser

syncron-lxc-ms:
  file.managed:
    - name: /etc/cron.d/makinastates_cloud_lxc_imgcron.presentsync
    - mode: 0750
    - user: root
    - group: root
    - contents: |
                {{settings.lxc.cron_minute}} {{settings.lxc.cron_hour}} * * * /usr/bin/mastersalt-run -linfo mc_lxc.sync_images > /dev/null
{% endif %}
