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
{% import "makina-states/_macros/services.jinja" as services with context %}
{{ salt['mc_macros.register']('services', 'php.phpfpm') }}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set locs = localsettings.locations %}
{% set phpSettings = services.phpSettings %}

include:
  - makina-states.services.php.common
{% if grains.get('lsb_distrib_id', '') == "Debian" %}
   # Include dotdeb repository for Debian
  - makina-states.localsettings.repository_dotdeb
{% endif %}

{# Manage php-fpm packages}
makina-php-pkgs:
  pkg.installed:
    - pkgs:
      - {{ phpSettings.packages.main }}
      - {{ phpSettings.packages.php_fpm }}
{% if phpSettings.modules.xdebug.install -%}
      - {{ phpSettings.packages.xdebug }}
{%- endif %}
{% if phpSettings.modules.apc.install -%}
      - {{ phpSettings.packages.apc }}
{%- endif %}

# remove default pool
makina-php-remove-default-pool:
  file.absent:
    - name : {{ phpSettings.etcdir }}/fpm/pool.d/www.conf

# --------- Pillar based php-fpm pools
{% from 'makina-states/services/php/php_macros.jinja' import pool with context %}
{% if 'register-pools' in phpSettings %}
{%   for site,siteDef in phpSettings['register-pools'].iteritems() %}
{%     do siteDef.update({'site': site}) %}
{%     do siteDef.update({'phpSettings': phpSettings}) %}
{{     pool(**siteDef) }}
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

makina-php-restart:
  service.running:
    - name: {{ phpSettings.service }}
    - enable: True
    # most watch requisites are linked here with watch_in
    - watch:
      # restart service in case of package install
      - pkg: makina-php-pkgs

# In most cases graceful reloads should be enough
makina-php-reload:
  service.running:
    - name: {{ phpSettings.service }}
    - require:
      - pkg: makina-php-pkgs
    - enable: True
    - reload: True
    # most watch requisites are linked here with watch_in

