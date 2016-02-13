{{salt['mc_macros.register']('services', 'php.phpfpm') }}
include:
  - makina-states.services.php.common
  - makina-states.services.php.phpfpm.prerequisites
  - makina-states.services.php.phpfpm.configuration
