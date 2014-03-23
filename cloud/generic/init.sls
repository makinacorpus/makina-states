{{- salt["mc_macros.register"]("services", "cloud.generic") }}
include:
  - makina-states.cloud.generic.controller
  - makina-states.cloud.generic.compute_node
  - makina-states.cloud.generic.vm
