# This file is an example of makina-states.services.php.phpfpm usage 
# @see php_example if you work with mod_php and not php-fpm
# TODO: document
include:
  # IMPORTANT: If you use Apache, include it BEFORE phpfpm, so that
  # we can detect apache is used and trigger the restart in case of mod_php removal
  - makina-states.services.http.apache
  #- makina-states.services.http.nginx
  - makina-states.services.php.phpfpm
extend:
  makina-apache-main-conf:
    mc_apache:
      - mpm: "{{ salt['pillar.get']('project-foobar-apache-mpm', 'event') }}"

# Adding mod_proxy_fcgi apache module (apache > 2.3)
# if you have apache 2.2 it's more complex, prefer nginx
makina-phpfpm-apache-modproxy-fcgi:
  mc_apache.include_module:
    - modules:
      - proxy_fcgi
    - require_in:
      - mc_apache: makina-apache-main-conf

{% from 'makina-states/services/php/php_defaults.jinja' import phpData with context %}

# Adding some php packages
my-phpfpm-other-modules:
  pkg.installed:
    - pkgs:
      - {{ phpData.packages.pear }}
      - {{ phpData.packages.apc }}
    - require_in:
      - pkg: makina-phpfpm-pkgs
# Ensuring some other are not there
# Note that you cannot remove a module listed in makina-mod_php-pkgs
my-phpfpm-removed-modules:
  pkg.removed:
    - pkgs:
      - {{ phpData.packages.memcached }}
    - require_in:
      - pkg: makina-phpfpm-pkgs

# Custom Apache Virtualhost
{% from 'makina-states/services/http/apache_defaults.jinja' import apacheData with context %}
{% from 'makina-states/services/http/apache_macros.jinja' import virtualhost with context %}
{{ virtualhost(apacheData = apacheData,
            site = salt['pillar.get']('project-foobar-apache-vh1-name', 'php.example.com'),
            small_name = salt['pillar.get']('project-foobar-apache-vh1-nickname', 'phpexample'),
            active = True,
            number = '990',
            log_level = salt['pillar.get']('project-foobar-apache-vh1-loglevel', 'info'),
            documentRoot = salt['pillar.get']('project-foobar-apache-vh1-docroot', '/srv/projects/example/foobar/www'),
            allow_htaccess = False) }}

# Custom php.ini settings set in the included apache virtualhost content file
