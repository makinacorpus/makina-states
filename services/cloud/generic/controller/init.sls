{{- salt["mc_macros.register"]("services", "cloud.cloud_controller") }}
include:
  - makina-states.controllers
  - makina-states.services.cloud.controller.hooks
  - makina-states.services.cloud.controller.prerequisites
  - makina-states.services.cloud.controller.layout
