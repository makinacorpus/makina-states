{# Apache httpd managment
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
#}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% import "makina-states/_macros/salt.jinja" as saltmac with context %}

{% set nodetypes = services.nodetypes %}
{% set localsettings = services.localsettings %}
{% set locs = localsettings.locations %}
{% set apacheSettings = services.apacheSettings %}

{% macro other_mpm_pkgs(mpm, indent='') %}
{% set opkgs = [] %}
{% for dmpm, packages in apacheSettings['mpm-packages'].items() %}
{%  if mpm != dmpm %}
{%    for pkg in packages %}{{indent}}      - {{pkg}}
{%    endfor %}
{%  endif %}
{% endfor %}
{% endmacro %}

{% macro mpm_pkgs(mpm, indent='') %}
{% set pkgs = apacheSettings['mpm-packages'].get(mpm, [] ) %}
{% for pkg in pkgs -%}{{indent}}      - {{ pkg }}
{% endfor -%}
{% endmacro %}

{% macro extend_switch_mpm(mpm) %}
  apache-uninstall-others-mpms:
    pkg.removed:
      - pkgs:
        {{ other_mpm_pkgs(mpm, indent='  ') }}
  apache-mpm:
    pkg.installed:
      - pkgs:
        {{ mpm_pkgs(mpm, indent='  ') }}
  makina-apache-main-conf:
    mc_apache.deployed:
      - mpm: {{mpm}}
{% endmacro %}

{% macro do(full=True) %}
{{ salt['mc_macros.register']('services', 'http.apache') }}
{% set apacheConfCheck = "salt://makina-states/_scripts/apacheConfCheck.sh" %}

{% set old_mode = (grains['lsb_distrib_id']=="Ubuntu" and grains['lsb_distrib_release']<13.10) or (grains['lsb_distrib_id']=="Debian" and grains['lsb_distrib_release']<=7.0) %}

include:
  - makina-states.services.http.apache-hooks

apache-uninstall-others-mpms:
  pkg.removed:
    - pkgs:
      {{ other_mpm_pkgs(services.apacheSettings.mpm) }}
    - require:
      - mc_proxy: makina-apache-post-pkgs
    - watch_in:
      - mc_proxy: makina-apache-post-inst
      - pkg: apache-mpm

apache-mpm:
  pkg.installed:
    - pkgs:
      {{ mpm_pkgs(services.apacheSettings.mpm) }}
    - require:
      - mc_proxy: makina-apache-post-pkgs
    - watch_in:
      - mc_proxy: makina-apache-post-inst

makina-apache-pkgs:
  pkg.installed:
    - watch:
      - mc_proxy: makina-apache-pre-inst
    - watch_in:
      - mc_proxy: makina-apache-post-inst
    - pkgs:
      {% for package in services.apacheSettings.packages %}
      - {{ package }}
      {% endfor %}
      - cronolog

## Apache Main Configuration ------------------
{# Default lists of included and excluded modules
extend theses two states if you need others
modules
#}
makina-apache-main-conf-included-modules:
  mc_apache.include_module:
    - modules:
      - rewrite
      - expires
      - headers
      - deflate
      - status
    - require_in:
      - mc_apache: makina-apache-main-conf

makina-apache-main-conf-excluded-modules:
  mc_apache.exclude_module:
    - modules:
{% if not services.apacheSettings.allow_bad_modules.negotiation %}
      - negotiation
{% endif %}
{% if not services.apacheSettings.allow_bad_modules.autoindex %}
      - autoindex
{% endif %}
{% if not services.apacheSettings.allow_bad_modules.cgid %}
      - cgid
{% endif %}
    - require_in:
      - mc_apache: makina-apache-main-conf
{# Read states documentation to alter main apache
# configuration
#}
makina-apache-main-conf:
  mc_apache.deployed:
    - version: {{ services.apacheSettings.version }}
    - mpm: {{ services.apacheSettings.mpm }}
    - log_level: {{ services.apacheSettings.log_level }}
    - watch:
      - mc_proxy: makina-apache-pre-conf
    # full service restart in case of changes
    - watch_in:
      # NO: this would prevent syntax check in case of error here
      # and errors here may be caused by syntax problems
      # - cmd: makina-apache-conf-syntax-check
      - mc_proxy: makina-apache-post-conf

makina-apache-settings:
  file.managed:
    - name: {{ services.apacheSettings.confdir }}/settings.local.conf
    - source: salt://makina-states/files/etc/apache2/conf.d/settings.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
        mode: "production"
        Timeout: "{{ services.apacheSettings.Timeout }}"
        KeepAlive: "{{ services.apacheSettings.KeepAlive }}"
        MaxKeepAliveRequests: "{{ services.apacheSettings.MaxKeepAliveRequests }}"
        KeepAliveTimeout: "{{ services.apacheSettings.KeepAliveTimeout }}"
        prefork_StartServers: "{{ services.apacheSettings.prefork.StartServers }}"
        prefork_MinSpareServers: "{{ services.apacheSettings.prefork.MinSpareServers }}"
        prefork_MaxSpareServers: "{{ services.apacheSettings.prefork.MaxSpareServers }}"
        prefork_MaxClients: "{{ services.apacheSettings.prefork.MaxClients }}"
        prefork_MaxRequestsPerChild: "{{ services.apacheSettings.prefork.MaxRequestsPerChild }}"
        worker_StartServers: "{{ services.apacheSettings.worker.StartServers }}"
        worker_MinSpareThreads: "{{ services.apacheSettings.worker.MinSpareThreads }}"
        worker_MaxSpareThreads: "{{ services.apacheSettings.worker.MaxSpareThreads }}"
        worker_ThreadLimit: "{{ services.apacheSettings.worker.ThreadLimit }}"
        worker_ThreadsPerChild: "{{ services.apacheSettings.worker.ThreadsPerChild }}"
        worker_MaxRequestsPerChild: "{{ services.apacheSettings.worker.MaxRequestsPerChild }}"
        worker_MaxClients: "{{ services.apacheSettings.worker.MaxClients }}"
        event_AsyncRequestWorkerFactor: "{{ services.apacheSettings.event.AsyncRequestWorkerFactor }}"
        log_level: "{{ services.apacheSettings.log_level }}"
{% if nodetypes.registry.is.devhost %}
    - context:
        mode: "dev"
{% endif %}
    - watch:
      - mc_proxy: makina-apache-post-inst
    # full service restart in case of changes
    - watch_in:
      - mc_proxy: makina-apache-pre-conf


{# Exemple to add a slug directly in apache configuration #}
makina-apache-main-extra-settings-example:
  file.accumulated:
    - name: extra-settings-master-conf
    - filename: {{ services.apacheSettings.confdir }}/settings.local.conf
    {# warning: keep the first line separated, multiline
     # folded yaml trick:
     # http://yaml.org/spec/1.2/spec.html#id2779048 #}
    - text: >
            # this is an example of thing added in master apache configuration

            # ServerLimit 1000

            # <Location />
                # Do something extraordinary
            # </Location>
    - watch_in:
      - file: makina-apache-settings

{# Define some basic security restrictions, like forbidden acces to all
# directories by default, switch off signatures protect .git, etc
# file is named _security to be read after the default security file
# in conf.d directory
#}
makina-apache-security-settings:
  file.managed:
    - watch:
      - mc_proxy: makina-apache-post-inst
    - name: {{ services.apacheSettings.confdir }}/_security.local.conf
    - source:
      - salt://makina-states/files/etc/apache2/conf.d/security.conf
    - user: root
    - group: root
    - mode: 644
    - watch:
       - mc_proxy: makina-apache-post-inst
    - watch_in:
       - mc_proxy: makina-apache-pre-conf

{# Exemple of error: using a second mc_apache.deployed would fail
# as only one main apache configuration can be defined
# per server
# Use ``extend`` on makina-apache-main-conf instead
#makina-apache-main-conf2:
#  mc_apache.deployed:
#    - version: 2.2
#    - log_level: warn
#    - watch:
#      - mc_proxy: makina-apache-post-inst
#}


{# Extra module additions and removal ----------------
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
#    - watch_in:
#      - mc_apache: makina-apache-main-conf
#
# Exemple: add negociation in excluded modules
#
#makina-apache-other-module-excluded:
#  mc_apache.exclude_module:
#    - modules:
#      - negotiation
#    - watch_in:
#      - mc_apache: makina-apache-main-conf
#}

# Directories settings -----------------
makina-apache-include-directory:
  file.directory:
    - user: root
    - group: www-data
    - mode: "2755"
    - makedirs: True
    - name: {{ services.apacheSettings.basedir }}/includes
    - watch:
       - mc_proxy: makina-apache-post-inst
    - watch_in:
       - mc_proxy: makina-apache-pre-conf

{# cronolog usage in {{ locs.var_dir }}/log/apache watchs a group write
# right which may not be present.
#}
makina-apache-default-log-directory:
  file.directory:
    - user: root
    - group: www-data
    - mode: "2770"
    - name: {{ services.apacheSettings.logdir }}
    - watch:
       - mc_proxy: makina-apache-post-inst
    - watch_in:
       - mc_proxy: makina-apache-pre-conf

{% if full %}
# Default Virtualhost managment -------------------------------------
{# Replace defaut Virtualhost by a more minimal default Virtualhost [1]
# this is the directory
#}
makina-apache-default-vhost-directory:
  file.directory:
    - user: root
    - group: www-data
    - mode: "2755"
    - makedirs: True
    - name: {{ locs.var_dir }}/www/default/
    - watch:
      - mc_proxy: makina-apache-post-inst
    - watch_in:
      - mc_proxy: makina-apache-pre-conf

{# Replace defaut Virtualhost by a more minimal default Virtualhost [2]
# this is the index.hml file
#}
makina-apache-default-vhost-index:
  file.managed:
    - name: {{ locs.var_dir }}/www/default/index.html
    - source:
      - salt://makina-states/files{{ locs.var_dir }}/www/default/default_vh.index.html
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
        mode: "production"
{% if nodetypes.registry.is.devhost %}
    - context:
        mode: "dev"
{% endif %}
    # full service restart in case of changes
    - watch:
      - mc_proxy: makina-apache-post-inst
    - watch_in:
      - mc_proxy: makina-apache-pre-conf

{# Replace defaut Virtualhost by a more minimal default Virtualhost [3]
# remove index.html coming from package
#}
makina-apache-remove-package-default-index:
  file.absent:
    - name : {{ locs.var_dir }}/www/index.html
    - watch:
      - mc_proxy: makina-apache-post-inst
    - watch_in:
      - mc_proxy: makina-apache-pre-conf

{# Replace defaut Virtualhost by a more minimal default Virtualhost [4]
# this is the virtualhost definition
#}
makina-apache-minimal-default-vhost:
  file.managed:
{% if old_mode %}
    - name: {{ services.apacheSettings.vhostdir }}/default
{% else %}
    - name: {{ services.apacheSettings.vhostdir }}/000-default.conf
{% endif %}
    - source:
      - salt://makina-states/files/etc/apache2/sites-available/default_vh.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
        log_level: "{{ services.apacheSettings.log_level }}"
        serveradmin_mail: "{{ services.apacheSettings.serveradmin_mail }}"
        mode: "production"
{% if nodetypes.registry.is.devhost %}
    - context:
        mode: "dev"
{% endif %}
    - watch:
      - file: makina-apache-default-vhost-index
      - mc_proxy: makina-apache-post-inst
    - watch_in:
      - mc_proxy: makina-apache-pre-conf


{% endif %}
#--- Configuration Check --------------------------------

{# Configuration checker, always run before restart of graceful restart
#}
makina-apache-conf-syntax-check:
  cmd.script:
    - source: {{ apacheConfCheck }}
    - stateful: True
    - watch:
      - mc_proxy: makina-apache-post-conf
    - watch_in:
      - mc_proxy: makina-apache-pre-restart

{# REMOVED, devhost is not using NFS anymore
#--- APACHE STARTUP WAIT DEPENDENCY --------------
{% if nodetypes.registry.is.devhost %}
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
    - watch_in:
      - file: makina-file_delay_services_for_srv
{% endif %}
#}
#--- MAIN SERVICE RESTART/RELOAD watchers --------------
makina-apache-restart:
  service.running:
    - name: {{ services.apacheSettings.service }}
    - enable: True
    # most watch requisites are linked here with watch_in
    - watch_in:
      - mc_proxy: makina-apache-post-restart
      # restart service in case of package install
    - watch:
      - mc_proxy: makina-apache-post-inst
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-post-conf
      - mc_proxy: makina-apache-pre-restart

{# In case of VirtualHosts change graceful reloads should be enough
#}
makina-apache-reload:
  service.running:
    - name: {{ services.apacheSettings.service }}
    - watch_in:
      - mc_proxy: makina-apache-post-restart
    - watch:
      - mc_proxy: makina-apache-post-inst
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-post-conf
      - mc_proxy: makina-apache-pre-restart
    - enable: True
    - reload: True
    # most watch requisites are linked here with watch_in

# Virtualhosts, here are the ones defined in pillar, if any ----------------
{#
# We loop on VH defined in pillar apache/virtualhosts, check the
# macro definition for the pillar dictionnary keys available. The
# virtualhosts key is set as the site name, and all keys are then
# added
# pillar example:
#apache-default-settings:
#  virtualhosts:
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
#}
{% from 'makina-states/services/http/apache_macros.jinja' import virtualhost with context %}
{% if 'virtualhosts' in services.apacheSettings -%}
{%   for site,siteDef in services.apacheSettings['virtualhosts'].iteritems() -%}
{%     do siteDef.update({'site': site}) %}
{{     virtualhost(**siteDef) }}
{%-   endfor %}
{%- endif %}

{% endmacro %}
{{ do(full=False) }}
