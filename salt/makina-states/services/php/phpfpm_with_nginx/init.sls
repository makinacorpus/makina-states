{{ salt['mc_macros.register']('services', 'php.phpfpm_with_nginx') }}
include:
  - makina-states.services.php.phpfpm_with_nginx.prerequisites
