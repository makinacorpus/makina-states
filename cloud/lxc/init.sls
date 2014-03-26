{{- salt["mc_macros.register"]("cloud", "lxc") }}
include:
  - makina-states.cloud.generic
  - makina-states.cloud.lxc.generate

