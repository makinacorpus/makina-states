{{- salt["mc_macros.register"]("services", "cloud.compute_node") }}
include:
  - makina-states.services.cloud.compute_node.pre-setup
  - makina-states.services.cloud.compute_node.setup
  - makina-states.services.cloud.compute_node.post-setup
