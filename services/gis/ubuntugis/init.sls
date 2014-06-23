{{ salt['mc_macros.register']('services', 'gis.ubuntugis') }}
include:
  - makina-states.services.gis.ubuntugis.prerequisites
  - makina-states.services.gis.ubuntugis.hooks
