{{- salt["mc_macros.register"]("services", "cloud.lxc") }}
include:
  - makina-states.services.cloud.lxc.hooks
  - makina-states.services.cloud.lxc.cloudcontroller
  - makina-states.services.cloud.lxc.images
  - makina-states.services.cloud.lxc.hosts
  - makina-states.services.cloud.lxc.containers
