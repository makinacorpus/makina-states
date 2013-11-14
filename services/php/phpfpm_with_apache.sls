# This file handle some associations of states
# between php-fpm and apache
# If you use nginx, do not include this state but the phpfpm_with_nginx.sls
include:
  - makina-states.services.http.apache

{% from 'makina-states/services/php/php_defaults.jinja' import phpData with context %}

makina-phpfpm-http-server-backlink:
  pkg.removed:
    - pkgs:
      - {{ phpData.packages.mod_php }}
      - {{ phpData.packages.mod_php_filter }}
      - {{ phpData.packages.php5_cgi }}
    # this must run BEFORE, else apt try to install one of mod_php/mod_phpfilter/php5_cgi
    # every time we remove one of them, except when fpm is already installed
    - require:
      - pkg: makina-phpfpm-pkgs
    # mod_php packages alteration needs an apache restart
    - watch_in:
       - service: makina-apache-restart
       - mc_apache: makina-apache-main-conf
