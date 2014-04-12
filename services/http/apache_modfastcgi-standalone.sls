{% import "makina-states/services/http/apache.sls" as apache with context %}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% set nodetypes = apache.nodetypes %}
{% set locs = salt['mc_locations.settings']() %}
{% set phpSettings = salt['mc_php.settings']() %}
{% set apacheSettings = salt['mc_apache.settings']() %}
{% macro fastcgi_common(
  full=True,
  shared_mode=apacheSettings.fastcgi_shared_mode,
  enabled=apacheSettings.fastcgi_enabled,
  project_root=apacheSettings.fastcgi_project_root,
  socket_directory = apacheSettings.fastcgi_socket_directory
) %}

{% if full %}
# Ensure that using php-fpm with apache we remove mod_php from Apache
makina-fastcgi-http-server-backlink:
  pkg.removed:
    - pkgs:
      - {{ phpSettings.packages.mod_php }}
      - {{ phpSettings.packages.mod_php_filter }}
      - {{ phpSettings.packages.php5_cgi }}
    # this must run BEFORE, else apt try to install one of mod_php/mod_phpfilter/php5_cgi
    # every time we remove one of them, except when fpm is already installed
    - require:
      - mc_proxy: makina-php-pre-inst
    # mod_php packages alteration needs an apache restart
    - watch_in:
      - mc_proxy: makina-apache-php-pre-conf
      - mc_proxy: makina-php-post-inst
{% endif %}


makina-fastcgi-apache-module_connect_fastcgi_mod_fastcgi_module_conf:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: {{ locs.conf_dir }}/apache2/mods-available/fastcgi.conf
    - source: salt://makina-states/files/etc/apache2/mods-available/fastcgi.conf
    - template: 'jinja'
    - defaults:
        enabled: {{ enabled }}
        project_root: '{{project_root}}'
        socket_directory:  '{{ socket_directory }}'
        extra: |
               {{salt['mc_utils.json_dump'](apacheSettings.fastcgi_params)}}
        {#  not used anymore
        shared_mode: {{ shared_mode }}
        #}
    - require:
      - mc_proxy: makina-php-post-inst
      - mc_proxy: makina-apache-php-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-php-post-conf
      - mc_proxy: makina-php-pre-restart

makina-fastcgi-apache-module_connect_fastcgi_notproxyfcgi:
  mc_apache.exclude_module:
    - modules:
      - proxy_fcgi
    - require:
      - mc_proxy: makina-php-post-inst
      - mc_proxy: makina-apache-php-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-php-post-conf
      - mc_proxy: makina-php-pre-restart
      - mc_apache: makina-apache-main-conf

makina-fastcgi-apache-module_connect_fastcgi:
  mc_apache.include_module:
    - modules:
      - fastcgi
      - actions
    - require:
      - mc_proxy: makina-php-post-inst
      - mc_proxy: makina-apache-php-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-php-post-conf
      - mc_proxy: makina-php-pre-restart
      - mc_apache: makina-apache-main-conf
{% endmacro %}

{% macro includes(full=True) %}
{% if full %}
  - makina-states.services.http.apache_modfastcgi
{% else %}
  - makina-states.services.http.apache_modfastcgi-standalone
{% endif %}
{% endmacro %}

{% macro do(full=False) %}
{{ salt['mc_macros.register']('services', 'http.apache_modfastcgi') }}
{#
include:
{{ common.common_includes(full=full, apache=True) }}
#}

include:
  - makina-states.services.php.php-apache-hooks
{% if full %}
  - makina-states.services.http.apache
{% else %}
  - makina-states.services.http.apache-standalone
{% endif %}

extend:
{{ apache.extend_switch_mpm(apacheSettings.multithreaded_mpm) }}

{{ fastcgi_common(full=full) }}
{% if full %}
# Adding mod_proxy_fcgi apache module (apache > 2.3)
# Currently mod_proxy_fcgi which should be the new default
# is commented, waiting for unix socket support
# So we keep using the old way
makina-fastcgi-apache-module_connect_fastcgi_mod_fastcgi_module:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - {{ apacheSettings.mod_packages.mod_fastcgi }}
    - require:
      - mc_proxy: makina-php-pre-inst
    - watch_in:
      - pkg: makina-fastcgi-http-server-backlink
      - mc_proxy: makina-php-post-inst
{% endif %}
{% endmacro %}

{{ do(full=False) }}
