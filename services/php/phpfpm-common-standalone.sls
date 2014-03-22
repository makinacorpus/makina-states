{% import "makina-states/services/php/common.sls" as common with context %}
{% import "makina-states/services/http/apache_modfastcgi.sls" as fastcgi with context %}
{% set services = common.services %}
{% set localsettings = common.localsettings %}
{% set nodetypes = common.nodetypes %}
{% set locs = common.locations %}
{% set phpSettings = common.phpSettings %}

{% macro do(full=True) %}

{% if full %}
{# Manage php-fpm packages @#}
makina-php-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - {{ phpSettings.packages.main }}
      - {{ phpSettings.packages.php_fpm }}
{% if phpSettings.modules.xdebug.install %}
      - {{ phpSettings.packages.xdebug }}
{% endif %}
{% if phpSettings.modules.apc.install %}
      - {{ phpSettings.packages.apc }}
{% endif %}
{% endif %}

# remove default pool
makina-phpfpm-remove-default-pool:
  file.absent:
    - name : {{ phpSettings.etcdir }}/fpm/pool.d/www.conf


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


{% endmacro %}
{{do(full=False)}}
