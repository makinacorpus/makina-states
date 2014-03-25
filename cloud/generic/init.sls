{{-salt["mc_macros.register"]("cloud", "generic") }}
include:
  - makina-states.cloud.generic.generate
  - makina-states.cloud.generic.install
