{{ salt['mc_macros.register']('services', 'http.apache_modfastcgi') }}
include:
  - makina-states.services.http.common
  - makina-states.services.http.apache_modfastcgi.prerequisites
  - makina-states.services.http.apache_modfastcgi.configuration
