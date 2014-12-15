{% set data = salt['mc_redis.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}
include:
  - makina-states.services.db.redis.hooks
  - makina-states.services.db.redis.service

{% for f in ['/etc/redisd.conf']%}
makina-redis-{{f}}:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files{{f}}
    - user: root
    - makedirs: true
    - group: root
    - mode: 744
    - template: jinja
    - defaults:
      data: |
            {{sdata}}
    - watch:
      - mc_proxy: redis-pre-conf
    - watch_in:
      - mc_proxy: redis-post-conf
{% endfor %}
