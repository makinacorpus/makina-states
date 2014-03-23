{{- salt["mc_macros.register"]("services", "cloud.saltify") }}

include:
  - makina-states.services.cloud.saltify.controller
  - makina-states.services.cloud.saltify.compute_node

