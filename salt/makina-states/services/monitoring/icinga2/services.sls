{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga2.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

include:
  - makina-states.services.monitoring.icinga2.hooks

icinga2-start:
  service.running:
    - name: icinga2
    - enable: True
    - watch:
      - mc_proxy: icinga2-pre-restart
    - watch_in:
      - mc_proxy: icinga2-post-restart

{% for f, key in data.ssh.items() %}
{% if key %}
icinga2-configuration-sshkey-{{f}}:
  file.managed:
    - name: /var/lib/nagios/{{f}}
    - source: ''
    - makedirs: true
    - user: nagios
    - group: nagios
    - mode: 700
    - watch:
      - mc_proxy: icinga2-pre-restart
    - watch_in:
      - mc_proxy: icinga2-post-restart
    - contents: |
                {{salt['mc_utils.indent'](key, spaces=16)}}
{% endif %}
{% endfor %}
