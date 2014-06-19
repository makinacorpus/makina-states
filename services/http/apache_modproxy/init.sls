{{ salt['mc_macros.register']('services', 'http.apache_modproxy') }}
include:
  - makina-states.services.http.apache
  - makina-states.services.http.apache_modproxy.configuration
