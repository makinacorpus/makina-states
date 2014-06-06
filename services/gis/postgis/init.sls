{{ salt['mc_macros.register']('services', 'gis.postgis') }}
include:
  - makina-states.services.db.postgresql
  - makina-states.services.gis.postgis.prerequisites
  - makina-states.services.gis.postgis.configuration
