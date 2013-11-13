# php-fpm: PHP as an independent fastcgi server
#
# Makina Corpus php-fpm Deployment main state
#
# For usage examples please check the file php_fpm_example.sls on this same directory
#
# Preferred way of altering default settings is to 
# create a state with a call to the jinja macro phppool()
# and to set some project's defaults piullar call on arguments given
#
# Defaults values not overriden in theses states calls are
# taken based on default_env grain from the php_defaults.jinja file
#
# consult pillar values with "salt '*' pillar.items"
# consult grains values with "salt '*' grains.items"
#

# Load defaults values -----------------------------------------

{% from 'makina-states/services/php/php_defaults.jinja' import phpData with context %}


makina-phpfpm-pkgs:
  pkg.installed:
    - pkgs:
      - {{ phpData.packages.main }}
      - {{ phpData.packages.php_fpm }}
{% if grains['makina.devhost'] %}
      - {{ phpData.packages.xdebug }}
{% endif %}

makina-phpfpm-exclude-modphp-pkg:
  pkg.removed:
    - pkgs:
      - {{ phpData.packages.mod_php }}
    - require_in:
      - pkg: makina-phpfpm-pkgs
{% if __salt__.has_key('apache.version') %}
    # mod_php packages alteration needs an apache restart
    # Problem, this state is maybe not available
    # nginx instead of apache?
    # apache state not included as a dependency...
    # so we use jinja to detect potential apache presence
    - watch_in:
       - service: makina-apache-restart
       - mc_apache: makina-apache-main-conf
{% endif %}
