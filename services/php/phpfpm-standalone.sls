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

{% macro do(full=False, apache=False)%}
{{ salt['mc_macros.register']('services', 'php.phpfpm') }}

include:
{{common.common_includes(full=full, apache=apache) }}
{% if apache %}
{{ fastcgi.includes(full=full) }}
{% endif %}

{% if full %}
{# Manage php-fpm packages @#}
makina-php-pkgs:
  pkg.installed:
    - pkgs:
      - {{ phpSettings.packages.main }}
      - {{ phpSettings.packages.php_fpm }}
{% if phpSettings.modules.xdebug.install %}
      - {{ phpSettings.packages.xdebug }}
{% endif %}
{% if phpSettings.modules.apc.install %}
      - {{ phpSettings.packages.apc }}
{% endif %}

# remove default pool
makina-phpfpm-remove-default-pool:
  file.absent:
    - name : {{ phpSettings.etcdir }}/fpm/pool.d/www.conf

{% endif %}
# --------- Pillar based php-fpm pools
{% if 'register-pools' in phpSettings %}
{%   for site,siteDef in phpSettings['register-pools'].iteritems() %}
{%     do siteDef.update({'site': site}) %}
{%     do siteDef.update({'phpSettings': phpSettings}) %}
{{     services.php.fpm_pool(**siteDef) }}
{%   endfor %}
{% endif %}

{# DEPRECATED devhosts are no longer using NFS
#--- PHP STARTUP WAIT DEPENDENCY --------------
{% if ('devhost' in nodetypes.registry.actives) %}
makina-add-php-in-waiting-for-nfs-services:
  file.accumulated:
    - name: list_of_services
    - filename: {{ locs.upstart_dir }}/delay_services_for_vagrant_nfs.conf
    - text: php5-fpm
    - require_in:
      - file: makina-file_delay_services_for_srv
{% endif %}
#}
#--- MAIN SERVICE RESTART/RELOAD watchers --------------

fpm-makina-php-restart:
  service.running:
    - name: {{ phpSettings.service }}
    - enable: True
    # most watch requisites are linked here with watch_in
    - watch:
      # restart service in case of package install
      - mc_proxy: makina-php-pre-restart
    - require_in:
      # restart service in case of package install
      - mc_proxy: makina-php-post-restart

# In most cases graceful reloads should be enough
fpm-makina-php-reload:
  service.running:
    - name: {{ phpSettings.service }}
    - watch:
      # reload service in case of package install
      - mc_proxy: makina-php-pre-restart
    - require_in:
      # reload service in case of package install
      - mc_proxy: makina-php-post-restart
    - enable: True
    - reload: True
    # most watch requisites are linked here with watch_in

{% if full and apache %}
# Adding mod_proxy_fcgi apache module (apache > 2.3)
# Currently mod_proxy_fcgi which should be the new default
# is commented, waiting for unix socket support
# So we keep using the old way
makina-phpfpm-apache-module_connect_phpfpm_mod_fastcgi_module:
  pkg.installed:
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
