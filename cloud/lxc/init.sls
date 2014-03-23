{{- salt["mc_macros.register"]("services", "cloud.lxc") }}
include:
  - makina-states.services.cloud.lxc.controller
  - makina-states.services.cloud.lxc.compute_node
  - makina-states.services.cloud.lxc.vm

