# php-fpm: PHP as an independent fastcgi server
#
# Makina Corpus php-fpm Deployment main state
#
# For usage examples please check the file php_fpm_example.sls on this same directory
#
# Preferred way of altering default settings is to
# create a state with a call to the jinja macro phppool()
# and to set some project's defaults pillar calls on arguments given
#
# Defaults values not overriden in theses states calls are
# taken based on default_env grain, pillar and such from the defaults defined
# in _modules/mc_php.py
#
# consult pillar values with "salt '*' pillar.items"
# consult grains values with "salt '*' grains.items"
#
{% import "makina-states/services/php/common.sls" as common with context %}
{% import "makina-states/services/http/apache_modfastcgi.sls" as fastcgi with context %}
{% set services = common.services %}
{% set localsettings = common.localsettings %}
{% set nodetypes = common.nodetypes %}
{% set locs = common.locations %}
{% set phpSettings = common.phpSettings %}

{% macro do(full=False, apache=False, noregister=False)%}
{% if not noregister %}
{{ salt['mc_macros.register']('services', 'php.phpfpm') }}
{% endif %}

include:
{{common.common_includes(full=full, apache=apache) }}
{% if full %}
  - makina-states.services.php.phpfpm-common
{% else %}
  - makina-states.services.php.phpfpm-common-standalone
{% endif %}
{% if apache %}
{{ fastcgi.includes(full=full) }}
{% endif %}
{% if full and apache %}
# Adding mod_proxy_fcgi apache module (apache > 2.3)
# Currently mod_proxy_fcgi which should be the new default
# is commented, waiting for unix socket support
# So we keep using the old way
makina-phpfpm-apache-module_connect_phpfpm_mod_fastcgi_module:
  pkg.{{localsettings.installmode}}:
    - pkgs:
      - {{ phpSettings.packages.php_fpm }}
    - require:
      - mc_proxy: makina-php-pre-inst
    - watch_in:
      {% if full %}
      - pkg: makina-fastcgi-http-server-backlink
      {% endif %}
      - mc_proxy: makina-php-post-inst
{% endif %}
{% endmacro %}
{{ do(full=False) }}
