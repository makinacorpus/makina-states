{{ salt['mc_macros.register']('services', 'db.rabbitmq') }}
include:
  - makina-states.services.queue.rabbitmq.prerequisites
  - makina-states.services.queue.rabbitmq.configuration
  - makina-states.services.queue.rabbitmq.services
  - makina-states.services.queue.rabbitmq.admin
  - makina-states.services.backup.dbsmartbackup

{# macro exports #}
{% import "makina-states/services/queue/rabbitmq/macros.sls" as macros with context %}
{% set rabbitmq_vhost = macros.rabbitmq_vhost %}
{% set rabbitmq_user = macros.rabbitmq_user %}

