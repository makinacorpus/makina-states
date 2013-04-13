include:
  - makina-states.controllers.hooks

{%- set locs = salt['mc_locations.settings']() %}
{%- set settings = salt['mc_salt.settings']() %}
{%- set pathid = salt['mc_utils.hash'](settings.msr, typ='md5') %}
{%- set bootsalt= '{0}/_scripts/boot-salt.sh'.format(settings.msr) %}

salt-salt-logrotate:
  file.managed:
    - template: jinja
    - name: {{ locs.conf_dir }}/logrotate.d/salt{{pathid}}.conf
    - source: salt://makina-states/files/etc/logrotate.d/salt.conf
    - require:
      - mc_proxy: dummy-pre-salt-checkouts
    - require_in:
      - mc_proxy: dummy-pre-salt-service-restart
