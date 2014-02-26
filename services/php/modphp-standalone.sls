{#
# mod_php: PHP as an apache module
#
# Makina Corpus mod_php Deployment main state
#
# For usage examples please check the file php_example.sls on this same directory
#
# TODO: review comment
# Preferred way of altering default settings is to set them in the apache Virtualhost
# We do not alter the main php.ini configuration file. This file is including
# php_defaults.jinja, you can reuse phpSettings dictionnary on your managed virtualhost template
# for php default values.
#
# If you want to add some more module include this file and reuse phpSettings.packages
# to find the right one (check php_defaults.jinja mapping)
#
# consult pillar values with "salt '*' pillar.items"
# consult grains values with "salt '*' grains.items"
#}
{% import "makina-states/services/php/common.sls" as common with context %}
{% set services = common.services %}
{% set localsettings = common.localsettings %}
{% set nodetypes = common.nodetypes %}
{% set locs = common.locations %}
{% set phpSettings = common.phpSettings %}
{% macro do(full=False)%}
{{ salt['mc_macros.register']('services', 'php.modphp') }}
include:
{{ common.common_includes(full=full, apache=True) }}
 
extend:
{{ common.apache.extend_switch_mpm('prefork') }}

{% if full %}
{# Manage php-fpm packages #}
makina-mod_php-exclude-fpm-pkg:
  pkg.removed:
    - pkgs:
      - {{ phpSettings.packages.php_fpm }}
      - {{ phpSettings.packages.mod_fcgid }}
      - {{ phpSettings.packages.php5_cgi }}
    - watch_in:
      - mc_proxy: makina-php-pre-inst

{# Manage mod_php packages #}
makina-php-pkgs:
  pkg.{{localsettings.installmode}}:
    - pkgs:
      - {{ phpSettings.packages.main }}
      - {{ phpSettings.packages.mod_php }}
      {% if phpSettings.modules.xdebug.install -%}
      - {{ phpSettings.packages.xdebug }}
      {%- endif %}
      {% if phpSettings.modules.apc.install -%}
      - {{ phpSettings.packages.apc }}
      {%- endif %}
    - require:
      - mc_proxy: makina-php-pre-inst
    {# mod_php packages alteration needs an apache restart #}
    - watch_in:
      - mc_proxy: makina-php-post-inst
{% endif %}
{% endmacro %}
{{ do(full=False)}}
