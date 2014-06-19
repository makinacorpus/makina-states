{{ salt['mc_macros.register']('services', 'http.apache_modfcgid') }}
include:
  - makina-states.services.http.common
  - makina-states.services.http.apache_modfcgid.prerequisites
  - makina-states.services.http.apache_modfcgid.configuration
