{%- set data = salt['mc_rabbitmq.settings']() %}
include:
  - makina-states.services.queue.rabbitmq.hooks
{% import "makina-states/services/queue/rabbitmq/macros.sls" as macros with context %}
{{macros.rabbitmq_user(data.rabbitmq.admin, data.rabbitmq.password, tags=['administrator'])}}
