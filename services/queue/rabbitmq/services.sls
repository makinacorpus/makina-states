include:
  - makina-states.services.queue.rabbitmq.hooks

makina-rabbitmq-service:
  service.running:
    - name: rabbitmq-server
    - enable: true
    - reload: true
    - watch:
      - mc_proxy: rabbitmq-pre-restart
    - watch_in:
      - mc_proxy: rabbitmq-post-restart

makina-rabbitmq-restart-service:
  service.running:
    - name: rabbitmq-server
    - enable: true
    - watch:
      - mc_proxy: rabbitmq-pre-hardrestart
    - watch_in:
      - mc_proxy: rabbitmq-post-hardrestart

rabbitmq-remove-guest:
  rabbitmq_user.absent:
    - name: guest
    - watch:
      - mc_proxy: rabbitmq-post-hardrestart
      - mc_proxy: rabbitmq-post-restart
