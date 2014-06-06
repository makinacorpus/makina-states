{{ salt['mc_macros.register']('services', 'gis.qgis') }}
include:
  - makina-states.services.gis.qgis.prerequisites
