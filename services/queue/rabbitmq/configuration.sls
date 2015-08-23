{% set data = salt['mc_rabbitmq.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}
include:
  - makina-states.services.queue.rabbitmq.hooks
  - makina-states.services.queue.rabbitmq.services

{% set modes = {
  '/etc/rabbitmq/rabbitmq.config': 700,
}
%}
{% for f in [
  '/etc/rabbitmq/rabbitmq.config',
  '/etc/default/rabbitmq-server',
  '/etc/logrotate.d/rabbitmq-server',
]%}
makina-rabbitmq-{{f}}:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files{{f}}
    - user: rabbitmq
    - mode: 750
    - makedirs: true
    - group: root
    - mode: {{modes.get(f, 744)}}
    - template: jinja
    - defaults:
      data: |
            {{sdata}}
    - watch:
      - mc_proxy: rabbitmq-pre-conf
    - watch_in:
      - mc_proxy: rabbitmq-post-conf
{% endfor %}

