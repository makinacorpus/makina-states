{% set data = salt['mc_redis.settings']() %}
include:
  - makina-states.services.db.redis.hooks
  - makina-states.services.db.redis.service

{% for f, tdata in data.templates.items() %}
makina-redis-{{f}}:
  file.managed:
    - name: {{f}}
    - source: "{{tdata.get('template', 'salt://makina-states/files'+f)}}"
    - user: "{{tdata.get('user', 'redis')}}"
    - group: "{{tdata.get('group', 'redis')}}"
    - mode: "{{tdata.get('mode', 750)}}"
    - makedirs: true
    - template: jinja
    - watch:
      - mc_proxy: redis-pre-conf
    - watch_in:
      - mc_proxy: redis-post-conf
{% endfor %}

makina-redis-localconf:
  file.managed:
    - name: /etc/redis/redis.local.conf
    - user: redis
    - group: redis
    - mode: 750
    - makedirs: true
    - source: ''
    - watch:
      - mc_proxy: redis-pre-conf
    - watch_in:
      - mc_proxy: redis-post-conf
