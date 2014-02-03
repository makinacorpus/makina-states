{#
# This file handle some associations of states
# between php-fpm and apache
# If you use nginx, do not include this state but the fcgid_with_nginx.sls
#
# WARNING, check the php_fpm_example state for detail on fastcgi.conf file
#
#}

{% import "makina-states/services/php/common.sls" as common with context %}
{% import "makina-states/services/php/fcgid-common.sls" as fcgid with context %}

{% set services = common.services %}
{% set localsettings = common.localsettings %}
{% set nodetypes = common.nodetypes %}
{% set locs = common.locations %}
{% set phpSettings = common.phpSettings %}

{% macro do(full=False)%}
{{ salt['mc_macros.register']('services', 'php.fcgid_with_apache') }}

include:
{{ fcgid_common.includes(full=full) }}

{% if full %}
# Adding mod_proxy_fcgi apache module (apache > 2.3)
# Currently mod_proxy_fcgi which should be the new default
# is commented, waiting for unix socket support
# So we keep using the old way
makina-fcgid-apache-module_connect_fcgid_mod_fastcgi_module:
  pkg.installed:
    - pkgs:
      - {{ phpSettings.packages.mod_fcgid }}
    - require:
      - mc_dummy: makina-php-pre-inst
    - watch_in:
      - pkg: makina-fcgid-http-server-backlink
      - mc_dummy: makina-php-post-inst
{% endif %}

{% endmacro %}
{{ do(full=False) }}
