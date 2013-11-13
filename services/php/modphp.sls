# mod_php: PHP as an apache module
#
# Makina Corpus mod_php Deployment main state
#
# For usage examples please check the file php_example.sls on this same directory
#
# Preferred way of altering default settings is to set them in the apache Virtualhost
# We do not alter the main php.ini configuration file. This file is including
# php_defaults.jinja, you can reuse phpData dictionnary on your managed virtualhost template
# for php default values.
#
# If you want to add some more module include this file and reuse phpData.packages
# to find the right one (check php_defaults.jinja mapping)
#
# consult pillar values with "salt '*' pillar.items"
# consult grains values with "salt '*' grains.items"
#
include:
  - makina-states.services.http.apache

# Load defaults values -----------------------------------------

{% from 'makina-states/services/php/php_defaults.jinja' import phpData with context %}

makina-mod_php-pkgs:
  pkg.installed:
    - pkgs:
      - {{ phpData.packages.main }}
      - {{ phpData.packages.mod_php }}
{% if grains['makina.devhost'] %}
      - {{ phpData.packages.xdebug }}
      - {{ phpData.packages.imagemagick }}
{% endif %}
    - require:
        - pkg: makina-apache-pkgs
    # mod_php packages alteration needs an apache restart
    - watch_in:
       - service: makina-apache-restart

makina-mod_php-exclude-fpm-pkg:
  pkg.removed:
    - pkgs:
      - {{ phpData.packages.php_fpm }}
    - require_in:
      - pkg: makina-mod_php-pkgs
