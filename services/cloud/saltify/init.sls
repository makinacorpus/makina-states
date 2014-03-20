{{- salt["mc_macros.register"]("services", "cloud.saltify") }}

include:
  - makina-states.services.cloud.saltify.cloudcontroller
  - makina-states.services.cloud.saltify.hosts

