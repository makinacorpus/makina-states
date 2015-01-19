{{- salt["mc_macros.register"]("cloud", "kvm") }}
include:
  - makina-states.cloud.generic
