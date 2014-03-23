{{- salt["mc_macros.register"]("services", "cloud.saltify") }}
include:
  - makina-states.cloud.saltify.controller
  - makina-states.cloud.saltify.compute_node
  - makina-states.cloud.saltify.vm

