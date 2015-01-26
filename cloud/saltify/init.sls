{{- salt["mc_macros.register"]("cloud", "saltify") }}
include:
  - makina-states.cloud.generic
