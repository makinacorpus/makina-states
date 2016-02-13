include:
  - makina-states.services.php.hooks
  - makina-states.services.http.apache.hooks

{% set apacheSettings = salt['mc_apache.settings']() %}
{% set phpSettings = salt['mc_php.settings']() %}
# Ensure that using php-fpm with apache we remove mod_php from Apache
makina-fastcgi-http-server-backlink:
  pkg.removed:
    - pkgs:
      - {{ phpSettings.packages.mod_php }}
      - {{ phpSettings.packages.mod_php_filter }}
      - {{ phpSettings.packages.php5_cgi }}
    # this must run BEFORE, else apt try to install one of mod_php/mod_phpfilter/php5_cgi
    # every time we remove one of them, except when fpm is already installed
    - require:
      - mc_proxy: makina-php-pre-inst
    # mod_php packages alteration needs an apache restart
    - watch_in:
      - mc_proxy: makina-apache-php-pre-conf
      - mc_proxy: makina-php-post-inst

# Adding mod_proxy_fcgi apache module (apache > 2.3)
# Currently mod_proxy_fcgi which should be the new default
# is commented, waiting for unix socket support
# So we keep using the old way
makina-fastcgi-apache-module_connect_fastcgi_mod_fastcgi_module:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - {{ apacheSettings.mod_packages.mod_fastcgi }}
    - require:
      - mc_proxy: makina-php-pre-inst
    - watch_in:
      - pkg: makina-fastcgi-http-server-backlink
      - mc_proxy: makina-php-post-inst
