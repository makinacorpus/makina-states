include:
  - makina-states.localsettings.timezone.hooks

{% set data = salt['mc_timezone.settings']() %}
{% if data.tz %}
makina-timezone-atz:
  file.absent:
    - onlyif: test -h /usr/share/zoneinfo/{{data.tz}}
    - name: /etc/timezone
    - watch_in:
      - mc_proxy: timezone-post-conf
    - watch:
      - mc_proxy: timezone-pre-conf
tz-conf:
  file.managed:
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: timezone-pre-conf
      - file: makina-timezone-atz
    - watch_in:
      - mc_proxy: timezone-post-conf
    - onlyif: test -e /usr/share/zoneinfo/{{data.tz}}
    - source: /usr/share/zoneinfo/{{data.tz}}
    - name: /etc/timezone
{% endif %} 
