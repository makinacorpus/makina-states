{{- salt["mc_macros.register"]("services", "cloud.cloudcontroller") }}
include:
  - makina-states.controllers
  - makina-states.services.cloud.cloudcontroller.hooks
  - makina-states.services.cloud.cloudcontroller.prerequisites
  - makina-states.services.cloud.cloudcontroller.layout
