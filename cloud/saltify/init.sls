{{- salt["mc_macros.register"]("cloud", "saltify") }}
include:
  - makina-states.cloud.saltify.controller
  - makina-states.cloud.saltify.compute_node
