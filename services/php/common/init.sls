{{ salt['mc_macros.register']('services', 'php.common') }}
include:
  - makina-states.services.http.common
  - makina-states.services.php.common.common
  - makina-states.services.php.hooks
