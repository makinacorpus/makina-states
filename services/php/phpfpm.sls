# php-fpm: PHP as an independent fastcgi server
#
# Makina Corpus php-fpm Deployment main state
#
# For usage examples please check the file php_fpm_example.sls on this same directory
#
# Preferred way of altering default settings is to 
# create a state with a call to the jinja macro phppool()
# and to set some project's defaults piullar call on arguments given
#
# Defaults values not overriden in theses states calls are
# taken based on default_env grain from the php_defaults.jinja file
#
# consult pillar values with "salt '*' pillar.items"
# consult grains values with "salt '*' grains.items"
#

include:
  - makina-states.services.php.common
{% if grains['lsb_distrib_id']=="Debian" %}
   # Include dotdeb repository for Debian
  - makina-states.services.php.repository_dotdeb
{% endif %}

# Load defaults values -----------------------------------------
{% from 'makina-states/services/php/php_defaults.jinja' import phpData with context %}

# Manage php-fpm packages

makina-php-pkgs:
  pkg.installed:
    - pkgs:
      - {{ phpData.packages.main }}
      - {{ phpData.packages.php_fpm }}
{% if phpData.modules.xdebug.install %}
      - {{ phpData.packages.xdebug }}
{% endif %}
{% if phpData.modules.apc.install %}
      - {{ phpData.packages.apc }}
{% endif %}

# remove default pool
makina-php-remove-default-pool:
  file.absent:
    - name : {{ phpData.etcdir }}/fpm/pool.d/www.conf

# --------- Pillar based php-fpm pools
{% from 'makina-states/services/php/php_macros.jinja' import pool with context %}
{% if 'register-pools' in phpData %}
{%   for site,siteDef in phpData['register-pools'].iteritems() %}
{%     do siteDef.update({'site': site}) %}
{%     do siteDef.update({'aphpData': phpData}) %}
{{     pool(**siteDef) }}
{%   endfor %}
{% endif %}


#--- PHP STARTUP WAIT DEPENDENCY --------------
{% if grains['makina.nodetype.devhost'] %}
# Delay start on vagrant dev host ------------
include:
  - makina-states.services.virt.mount_upstart_waits

makina-add-php-in-waiting-for-nfs-services:
  file.accumulated:
    - name: list_of_services
    - filename: /etc/init/delay_services_for_vagrant_nfs.conf
    - text: php5-fpm
    - require_in:
      - file: makina-file_delay_services_for_srv
{% endif %}

#--- MAIN SERVICE RESTART/RELOAD watchers --------------

makina-php-restart:
  service.running:
    - name: {{ phpData.service }}
    - enable: True
    # most watch requisites are linked here with watch_in
    - watch:
      # restart service in case of package install
      - pkg: makina-php-pkgs

# In most cases graceful reloads should be enough
makina-php-reload:
  service.running:
    - name: {{ phpData.service }}
    - require:
      - pkg: makina-php-pkgs
    - enable: True
    - reload: True
    # most watch requisites are linked here with watch_in
