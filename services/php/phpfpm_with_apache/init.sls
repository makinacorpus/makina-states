{{ salt['mc_macros.register']('services', 'php.phpfpm_with_apache') }}
include:
  - makina-states.services.http.apache
  - makina-states.services.php.phpfpm_with_apache.prerequisites
  - makina-states.services.php.phpfpm_with_apache.configuration
