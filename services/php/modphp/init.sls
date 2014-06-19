{{ salt['mc_macros.register']('services', 'php.modphp') }}
include:
  - makina-states.services.http.apache
  - makina-states.services.php.common
  - makina-states.services.php.modphp.prerequisites
  - makina-states.services.php.modphp.configuration
