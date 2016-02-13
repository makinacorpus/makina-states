{{ salt['mc_macros.register']('services', 'sound.mumble') }}
include:
  - makina-states.services.sound.mumble.prerequisites
  - makina-states.services.sound.mumble.configuration
  - makina-states.services.sound.mumble.services
