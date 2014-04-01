{{ salt['mc_macros.register']('services', 'http.nginx') -}}
include:
  - makina-states.services.http.nginx.prerequisites
  - makina-states.services.http.nginx.configuration
  - makina-states.services.http.nginx.vhosts
  - makina-states.services.http.nginx.hooks
  - makina-states.services.http.nginx.services

