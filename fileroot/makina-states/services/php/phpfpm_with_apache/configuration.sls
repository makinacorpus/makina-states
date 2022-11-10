{% set phpSettings = salt['mc_php.settings']() %}
include:
  - makina-states.services.http.apache_modfastcgi
  - makina-states.services.php.phpfpm

{# goal is to be sure to have modfastcgi
  and fpm configured.
  It is up to a project to configure itself,
  and this project can use the macro "fpm_pool" to
  make easily a new fpmpool to use
#}
