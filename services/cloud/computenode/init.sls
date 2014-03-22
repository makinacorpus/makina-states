{{- salt["mc_macros.register"]("services", "cloud.cloudcontroller") }}
include:
  - makina-states.services.cloud.computenode.install-reverseproxy
