# Apache httpd managment
#
# Makina Corpus Apache Deployment main state
#
# For usage examples please check the file apache_example.sls on this same directory
#
# Preferred way of altering default settings is to extend the states
# makina-apache-main-conf and makina-apache-settings (explained in the apache_example state file):
#
# But configuration can also be made in the pillar, to alter
# default values without using states, or in complement of theses states (explained in pillar.sample)
#
#
# consult pillar values with "salt '*' pillar.items"
# consult grains values with "salt '*' grains.items"
#
# TODO: alter mod_status conf to allow only localhost,monitoring some user defined IP,  ExtendedStatus Off
# TODO: SSL VH
# TODO: detect invalid links in sites-enabled and remove them
# apache 2.4: EnableSendfile On, NameVirtualHost deprecated,  RewriteLog and RewriteLogLevel-> LogLevel rewrite:debug
# enable and configure mod_reqtimeout

{% set msr='/srv/salt/makina-states' %}
{% set apacheConfCheck = "file://"+msr+"/_scripts/apacheConfCheck.sh" %}

# Load defaults values -----------------------------------------

{% from 'makina-states/services/http/apache_defaults.jinja' import apacheData with context %}

{% set old_mode = (grains['lsb_distrib_id']=="Ubuntu" and grains['lsb_distrib_release']<13.10) or (grains['lsb_distrib_id']=="Debian" and grains['lsb_distrib_release']<=7.0) %}

makina-apache-pkgs:
  pkg.installed:
    - pkgs:
      - {{ apacheData.package }}
      - cronolog

# Apache Main Configuration ------------------
# Read states documentation to alter main apache
# configuration
makina-apache-main-conf:
  mc_apache.deployed:
    - version: {{ apacheData.version }}
    - mpm: {{ apacheData.mpm }}
    # see also mc_apache.include_module
    # and mc_apache.exclude_module
    # to alter theses lists from
    # other states (examples below)
    - modules_excluded:
      - negotiation
      - autoindex
      - cgid
    - modules_included:
      - rewrite
      - expires
      - headers
      - deflate
      - status
    - log_level: {{ apacheData.log_level }}
    - require:
      - pkg: makina-apache-pkgs
    # full service restart in case of changes
    - watch_in:
       # NO: this would prevent syntax check in case of error here
       # and errors here may be caused by syntax problems
       # - cmd: makina-apache-conf-syntax-check
       - service: makina-apache-restart

makina-apache-settings:
  file.managed:
    - name: {{ apacheData.confdir }}/settings.local.conf
    - source: salt://makina-states/files/etc/apache2/conf.d/settings.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
        mode: "production"
        Timeout: "{{ apacheData.Timeout }}"
        KeepAlive: "{{ apacheData.KeepAlive }}"
        MaxKeepAliveRequests: "{{ apacheData.MaxKeepAliveRequests }}"
        KeepAliveTimeout: "{{ apacheData.KeepAliveTimeout }}"
        prefork_StartServers: "{{ apacheData.prefork.StartServers }}"
        prefork_MinSpareServers: "{{ apacheData.prefork.MinSpareServers }}"
        prefork_MaxSpareServers: "{{ apacheData.prefork.MaxSpareServers }}"
        prefork_MaxClients: "{{ apacheData.prefork.MaxClients }}"
        prefork_MaxRequestsPerChild: "{{ apacheData.prefork.MaxRequestsPerChild }}"
        worker_StartServers: "{{ apacheData.worker.StartServers }}"
        worker_MinSpareThreads: "{{ apacheData.worker.MinSpareThreads }}"
        worker_MaxSpareThreads: "{{ apacheData.worker.MaxSpareThreads }}"
        worker_ThreadLimit: "{{ apacheData.worker.ThreadLimit }}"
        worker_ThreadsPerChild: "{{ apacheData.worker.ThreadsPerChild }}"
        worker_MaxRequestsPerChild: "{{ apacheData.worker.MaxRequestsPerChild }}"
        worker_MaxClients: "{{ apacheData.worker.MaxClients }}"
        event_AsyncRequestWorkerFactor: "{{ apacheData.event.AsyncRequestWorkerFactor }}"
        log_level: "{{ apacheData.log_level }}"
{% if grains['makina.nodetype.devhost'] %}
    - context:
        mode: "dev"
{% endif %}
    - require:
      - pkg.installed: makina-apache-pkgs
    # full service restart in case of changes
    - watch_in:
       - cmd: makina-apache-conf-syntax-check
       - service: makina-apache-restart

makina-apache-main-extra-settings-example:
  file.accumulated:
    - name: extra-settings-master-conf
    - filename: {{ apacheData.confdir }}/settings.local.conf
    - text: |
        '# this is an example of thing added in master apache configuration'
        '# ServerLimit 1000'
        '# <Location />'
        '# </Location>'
    - watch_in:
      - file: makina-apache-settings

# Define some basic security restrictions, like forbidden acces to all
# directories by default, switch off signatures protect .git, etc
# file is named _security to be read after the default security file
# in conf.d directory
makina-apache-security-settings:
  file.managed:
    - require:
      - pkg.installed: makina-apache-pkgs
    - name: {{ apacheData.confdir }}/_security.local.conf
    - source:
      - salt://makina-states/files/etc/apache2/conf.d/security.conf
    - user: root
    - group: root
    - mode: 644
    - watch_in:
       - cmd: makina-apache-conf-syntax-check
       - service: makina-apache-restart

# Exemple of error: using a second mc_apache.deployed would fail
# as only one main apache configuration can be defined
# per server
# Use ``extend`` on makina-apache-main-conf instead
#makina-apache-main-conf2:
#  mc_apache.deployed:
#    - version: 2.2
#    - log_level: warn
#    - require:
#      - pkg: makina-apache-pkgs



# Extra module additions and removal ----------------
# Theses (valid) examples show you how
# to alter the modules_excluded and
# modules_included lists
#
# Exemple: add 3 modules
#
#makina-apache-other-module-included:
#  mc_apache.include_module:
#    - modules:
#      - deflate
#      - status
#      - cgid
#    - require_in:
#      - mc_apache: makina-apache-main-conf
#
# Exemple: add negociation in excluded modules
#
#makina-apache-other-module-excluded:
#  mc_apache.exclude_module:
#    - modules:
#      - negotiation
#    - require_in:
#      - mc_apache: makina-apache-main-conf

# Directories settings -----------------

makina-apache-include-directory:
  file.directory:
    - user: root
    - group: www-data
    - mode: "2755"
    - makedirs: True
    - name: {{ apacheData.basedir }}/includes
    - require:
       - pkg: makina-apache-pkgs
    - require_in:
       - service: makina-apache-restart
       - service: makina-apache-reload

# cronolog usage in /var/log/apache requires a group write
# right which may not be present.
makina-apache-default-log-directory:
  file.directory:
    - user: root
    - group: www-data
    - mode: "2770"
    - name: {{ apacheData.logdir }}
    - require:
       - pkg: makina-apache-pkgs
    - require_in:
       - service: makina-apache-restart
       - service: makina-apache-reload

# Default Virtualhost managment -------------------------------------
# Replace defaut Virtualhost by a more minimal default Virtualhost [1]
# this is the directory
makina-apache-default-vhost-directory:
  file.directory:
    - user: root
    - group: www-data
    - mode: "2755"
    - makedirs: True
    - name: /var/www/default/
    - require:
       - pkg: makina-apache-pkgs
    - require_in:
       - service: makina-apache-restart

# Replace defaut Virtualhost by a more minimal default Virtualhost [2]
# this is the index.hml file
makina-apache-default-vhost-index:
  file.managed:
    - require:
      - pkg.installed: makina-apache-pkgs
    - name: /var/www/default/index.html
    - source:
      - salt://makina-states/files/var/www/default/default_vh.index.html
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
        mode: "production"
{% if grains['makina.nodetype.devhost'] %}
    - context:
        mode: "dev"
{% endif %}
    # full service restart in case of changes
    - watch_in:
       - cmd: makina-apache-conf-syntax-check
       - service: makina-apache-restart

# Replace defaut Virtualhost by a more minimal default Virtualhost [3]
# remove index.html coming from package
makina-apache-remove-package-default-index:
  file.absent:
    - name : /var/www/index.html

  
# Replace defaut Virtualhost by a more minimal default Virtualhost [4]
# this is the virtualhost definition
makina-apache-minimal-default-vhost:
  file.managed:
    - require:
      - pkg: makina-apache-pkgs
      - file: makina-apache-default-vhost-index
{% if old_mode %}
    - name: {{ apacheData.vhostdir }}/default
{% else %}
    - name: {{ apacheData.vhostdir }}/000-default.conf
{% endif %}
    - source:
      - salt://makina-states/files/etc/apache2/sites-available/default_vh.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
        log_level: "{{ apacheData.log_level }}"
        serveradmin_mail: "{{ apacheData.serveradmin_mail }}"
        mode: "production"
{% if grains['makina.nodetype.devhost'] %}
    - context:
        mode: "dev"
{% endif %}
    - watch_in:
       - cmd: makina-apache-conf-syntax-check
       - service: makina-apache-restart

#--- Configuration Check --------------------------------

# Configuration checker, always run before restart of graceful restart
makina-apache-conf-syntax-check:
  cmd.script:
    - source: {{apacheConfCheck}}
    - stateful: True
    - require:
      - pkg: makina-apache-pkgs
    - require_in:
       - service: makina-apache-restart
       - service: makina-apache-reload

#--- APACHE STARTUP WAIT DEPENDENCY --------------
{% if grains['makina.nodetype.devhost'] %}
#
# On a vagrant VM we certainly should wait until NFS mount
# before starting the web server. Chances are that this NFS mount
# contains our documentroots and log directories
# Delay start on vagrant dev host ------------
include:
  - makina-states.services.virt.mount_upstart_waits

makina-add-apache-in-waiting-for-nfs-services:
  file.accumulated:
    - name: list_of_services
    - filename: /etc/init/delay_services_for_vagrant_nfs.conf
    - text: apache2
    - require_in:
      - file: makina-file_delay_services_for_srv
{% endif %}

#--- MAIN SERVICE RESTART/RELOAD watchers --------------

makina-apache-restart:
  service.running:
    - name: {{ apacheData.service }}
    - enable: True
    # most watch requisites are linked here with watch_in
    - watch:
      # restart service in case of package install
      - pkg: makina-apache-pkgs

# In case of VirtualHosts change graceful reloads should be enough
makina-apache-reload:
  service.running:
    - name: {{ apacheData.service }}
    - require:
      - pkg: makina-apache-pkgs
    - enable: True
    - reload: True
    # most watch requisites are linked here with watch_in

# Virtualhosts, here are the ones defined in pillar, if any ----------------
#
# We loop on VH defined in pillar apache/register-sites, check the
# macro definition for the pillar dictionnary keys available. The
# register-sites key is set as the site name, and all keys are then
# added
# pillar example:
#apache-default-settings:
#  register-sites:
#     example.com:
#        active: False
#        small_name: example
#        number: 200
#        documentRoot: /srv/foo/bar/www
#      example.foo.com:
#        active: False
#        number: 202
#
# Note that the best way to make a VH is not the pillar, but
# loading the macro as we do here and use virtualhost()) call
# in a state.
# Then use the pillar to alter your default parameters given to this call
#
{% from 'makina-states/services/http/apache_macros.jinja' import virtualhost with context %}
{% if 'register-sites' in apacheData %}
{%   for site,siteDef in apacheData['register-sites'].iteritems() %}
{%     do siteDef.update({'site': site}) %}
{%     do siteDef.update({'apacheData': apacheData}) %}
{{     virtualhost(**siteDef) }}
{%   endfor %}
{% endif %}

