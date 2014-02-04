# This file is an example of makina-states.services.php.modphp usage
# @see php_fpm_example if you work with php-fpm
# how to enforce apache in mmp prefork (limitation of mod_php)
# create a basic apache virtualhost, see apache_example.sls for details
# how to add php setings in your apache virtualhost
# @see also the pillar.sample file
#
## remember theses 4 rules for extend:
##1-Always include the SLS being extended with an include declaration
##2-Requisites (watch and require) are appended to, everything else is overwritten
##3-extend is a top level declaration, like an ID declaration, cannot be declared twice in a single SLS
##4-Many IDs can be extended under the extend declaration

{% import "makina-states/_macros/services.jinja" as services with context %}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set locs = localsettings.locations %}
{% set php = services.pĥp %}
{% set apache = services.apache %}

include:
  - makina-states.services.php.modphp

# Adding some php packages
my-php-other-modules:
  pkg.installed:
    - pkgs:
      - {{ phpData.packages.pear }}
    - require_in:
      - mc_proxy: makina-apache-php-post-inst
# Ensuring some other are not there
# Note that you cannot remove a module listed in makina-mod_php-pkgs
my-php-removed-modules:
  pkg.removed:
    - pkgs:
      - {{ phpData.packages.memcached }}
    - require_in:
      - mc_proxy: makina-apache-php-post-inst

# Custom Apache Virtualhost
{% from 'makina-states/services/http/apache_defaults.jinja' import apacheData with context %}
{% from 'makina-states/services/http/apache_macros.jinja' import virtualhost with context %}
{{ apache.virtualhost(apacheData = apacheData,
                      site = salt['pillar.get']('project-foobar-apache-vh1-name', 'php.example.com'),
                      small_name = salt['pillar.get']('project-foobar-apache-vh1-nickname', 'phpexample'),
                      active = True,
                      number = '990',
                      log_level = salt['pillar.get']('project-foobar-apache-vh1-loglevel', 'info'),
                      documentRoot = salt['pillar.get']('project-foobar-apache-vh1-docroot', '/srv/projects/example/foobar/www'),
                      allow_htaccess = False) }}

# Custom php.ini settings set in the included apache virtualhost content file
