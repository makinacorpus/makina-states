{% import "makina-states/services/php/common.sls" as common with context %}
{% set services = common.services %}
{% set localsettings = common.localsettings %}
{% set nodetypes = common.nodetypes %}
{% set locs = common.locs %}
{% set phpSettings = common.phpSettings %}
{% macro fcgid_common(
  full=True,
  shared_mode=True,
  enabled=True,
  project_root='',
  socket_directory = '/var/lib/apache2/fastcgi'
) %}

{% if full %}
# Ensure that using php-fpm with apache we remove mod_php from Apache
makina-fcgid-http-server-backlink:
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

makina-fcgid-apache-module_connect_fcgid_mod_fastcgi_module_conf:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: {{ locs.conf_dir }}/apache2/mods-available/fastcgi.conf
    - source: salt://makina-states/files/etc/apache2/mods-available/fastcgi.conf
    - template: 'jinja'
    - defaults:
        enabled: {{ enabled }}
        shared_mode: {{ shared_mode }}
        project_root: '{{project_root}}'
        socket_directory:  '{{socket_directory }}'
    - require:
      - mc_proxy: makina-php-post-inst
      - mc_proxy: makina-apache-php-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-php-post-conf
      - mc_proxy: makina-php-pre-restart

makina-fastcgid-apache-module_connect_fastcgid_notproxyfcgi:
  mc_apache.exclude_module:
    - modules:
      - proxy_fcgi
    - require:
      - mc_proxy: makina-php-post-inst
      - mc_proxy: makina-apache-php-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-php-post-conf
      - mc_proxy: makina-php-pre-restart

makina-fastcgid-apache-module_connect_fastcgid:
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
{% endmacro %}

{% fcgid_includes(full=True) %}
{% if full %}
  - makina-states.services.php.fcgid_common
{% else %}
  - makina-states.services.php.fcgid_common-standalone
{% endif %}
{% endmacro %}

{% macro do(full=False) %}
include:
{{ common.common_includes(full=full, apache=True) }}

{{ fcgid_common(full=full) }}

{% endmacro %}

{{ do(full=False) }}
