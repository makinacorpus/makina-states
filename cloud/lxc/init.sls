{{- salt["mc_macros.register"]("cloud", "lxc") }}
include:
  - makina-states.cloud.generic
  - makina-states.cloud.lxc.controller
  - makina-states.cloud.lxc.compute_node
  - makina-states.cloud.lxc.vm

