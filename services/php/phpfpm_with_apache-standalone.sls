{#
# This file handle some associations of states
# between php-fpm and apache
# If you use nginx, do not include this state but the phpfpm_with_nginx.sls
#
# WARNING, check the php_fpm_example state for detail on fastcgi.conf file
#
#}

{% import "makina-states/services/php/phpfpm.sls" as phpfpm with context %}
{% import "makina-states/services/php/common.sls" as common with context %}
{% set nodetypes_registry = salt['mc_nodetypes.registry']() %}
{% set locs = salt['mc_locations.settings']() %}
{% set phpSettings = salt['mc_php.settings']() %}

{% macro do(full=False)%}
{{ salt['mc_macros.register']('services', 'php.phpfpm_with_apache') }}
{{ phpfpm.do(full=full, apache=True, noregister=True) }}
{% endmacro %}
{{ do(full=False) }}
