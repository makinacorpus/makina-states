# Adding mod_proxy_fcgi apache module (apache > 2.3)
# Currently mod_proxy_fcgi which should be the new default
# is commented, waiting for unix socket support
# So we keep using the old way
{% set phpSettings = salt['mc_php.settings']() %}

include:
  - makina-states.services.php.hooks

makina-phpfpm-apache-module_connect_phpfpm_mod_fastcgi_module:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - {{ phpSettings.packages.php_fpm }}
    - require:
      - mc_proxy: makina-php-pre-inst
    - watch_in:
      - pkg: makina-fastcgi-http-server-backlink
      - mc_proxy: makina-php-post-inst
