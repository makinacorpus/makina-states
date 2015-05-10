{{- salt["mc_macros.register"]("cloud", "docker") }}
include:
  - makina-states.cloud.generic
