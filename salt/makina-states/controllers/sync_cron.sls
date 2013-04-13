include:
  - makina-states.controllers.hooks
{%- set settings = salt['mc_salt.settings']() %}
{%- set pathid = salt['mc_utils.hash'](settings.msr, typ='md5') %}
{%- set bootsalt= '{0}/_scripts/boot-salt.sh'.format(settings.msr) %}
salt-crons:
  file.managed:
    - name: /etc/cron.d/salt{{pathid}}
    - require:
      - mc_proxy: dummy-pre-salt-checkouts
    - require_in:
      - mc_proxy: dummy-pre-salt-service-restart
    - source: ''
    - mode: 750
    - user: root
    - contents: |
                # salt code synchronization job
                {{settings.cron_sync_minute}} {{settings.cron_sync_hour}} * * * root {{bootsalt}} --synchronize-code --quiet -C --no-colors
