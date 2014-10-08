{{ salt['mc_macros.register']('services', 'cache.memcached') }}
include:
  - makina-states.services.cache.memcached.hooks
  - makina-states.services.cache.memcached.prerequisites
  - makina-states.services.cache.memcached.configuration
  - makina-states.services.cache.memcached.services
