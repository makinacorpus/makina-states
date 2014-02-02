{#
# This file handle some associations of states
# between php-fpm and apache
# If you use nginx, do not include this state but the phpfpm_with_nginx.sls
#
# WARNING, check the php_fpm_example state for detail on fastcgi.conf file
#
#}

{% from 'makina-states/services/php/php_defaults.jinja' import phpData with context %}
{% import "makina-states/services/php/common.sls" as common with context %}
{% set services = common.services %}
{% set localsettings = common.localsettings %}
{% set nodetypes = common.nodetypes %}
{% set locs = common.locations %}
{% set phpSettings = common.phpSettings %}

{% macro do(full=False)%}
{{ salt['mc_macros.register']('services', 'php.phpfpm_with_apache') }}

include:
{{ common.apache_includes(full=full) }}
{{ common.includes(full=full) }}

{{ common.apache_hooks(full=full) }}
{{ common.do(full=full) }}

{% if full %}
# Adding mod_proxy_fcgi apache module (apache > 2.3)
# Currently mod_proxy_fcgi which should be the new default
# is commented, waiting for unix socket support
# So we keep using the old way
makina-phpfpm-apache-module_connect_phpfpm_mod_fastcgi_module:
  pkg.installed:
    - pkgs:
      - libapache2-mod-fastcgi
    - require:
      - mc_dummy: makina-php-pre-inst
    - watch_in:
      - pkg: makina-phpfpm-http-server-backlink
      - mc_dummy: makina-php-post-inst

# Ensure that using php-fpm with apache we remove mod_php from Apache
makina-phpfpm-http-server-backlink:
  pkg.removed:
    - pkgs:
      - {{ phpData.packages.mod_php }}
      - {{ phpData.packages.mod_php_filter }}
      - {{ phpData.packages.php5_cgi }}
    # this must run BEFORE, else apt try to install one of mod_php/mod_phpfilter/php5_cgi
    # every time we remove one of them, except when fpm is already installed
    - require:
      - mc_dummy: makina-php-pre-inst
    # mod_php packages alteration needs an apache restart
    - watch_in:
      - mc_dummy: makina-apache-php-pre-conf
      - mc_dummy: makina-php-post-inst

{% endif %}

makina-phpfpm-apache-module_connect_phpfpm_mod_fastcgi_module_conf:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: {{ locs.conf_dir }}/apache2/mods-available/fastcgi.conf
    - source: salt://makina-states/files/etc/apache2/mods-available/fastcgi.conf
    - template: 'jinja'
    - defaults:
        shared_mode: True
        project_root: ''
        shared_mode: True
        socket_directory: '/var/lib/apache2/fastcgi'
    - require:
      - mc_dummy: makina-php-post-inst
      - mc_dummy: makina-apache-php-pre-conf
    - watch_in:
      - mc_dummy: makina-apache-php-post-conf
      - mc_dummy: makina-php-pre-restart

makina-phpfpm-apache-module_connect_phpfpm_notproxyfcgi:
  mc_apache.exclude_module:
    - modules:
      - proxy_fcgi
    - require:
      - mc_dummy: makina-php-post-inst
      - mc_dummy: makina-apache-php-pre-conf
    - watch_in:
      - mc_dummy: makina-apache-php-post-conf
      - mc_dummy: makina-php-pre-restart

makina-phpfpm-apache-module_connect_phpfpm:
  mc_apache.include_module:
    - modules:
      - fastcgi
      - actions
    - require:
      - mc_dummy: makina-php-post-inst
      - mc_dummy: makina-apache-php-pre-conf
    - watch_in:
      - mc_dummy: makina-apache-php-post-conf
      - mc_dummy: makina-php-pre-restart

{% endmacro %}
{{ do(full=False) }}
