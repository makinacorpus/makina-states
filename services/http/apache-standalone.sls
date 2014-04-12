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
# TODO: SSL VH
# TODO: detect invalid links in sites-enabled and remove them
# apache 2.4: EnableSendfile On, NameVirtualHost deprecated,  RewriteLog and RewriteLogLevel-> LogLevel rewrite:debug
# enable and configure mod_reqtimeout
#}
{% import "makina-states/_macros/apache.jinja" as apache with context %}

{% set nodetypes_registry = salt['mc_nodetypes.registry']() %}
{% set localsettings = salt['mc_localsettings.settings']() %}
{% set locs = salt['mc_localsettings.settings']()['locations'] %}
{% set apacheSettings = salt['mc_apache.settings']() %}

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
    pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
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
      {{ other_mpm_pkgs(salt['mc_apache.settings']().mpm) }}
    - require:
      - mc_proxy: makina-apache-post-pkgs
    - watch_in:
      - mc_proxy: makina-apache-post-inst
      - pkg: apache-mpm

apache-mpm:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      {{ mpm_pkgs(salt['mc_apache.settings']().mpm) }}
    - require:
      - mc_proxy: makina-apache-post-pkgs
    - watch_in:
      - mc_proxy: makina-apache-post-inst

makina-apache-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - watch:
      - mc_proxy: makina-apache-pre-inst
    - watch_in:
      - mc_proxy: makina-apache-post-inst
    - pkgs:
      {% for package in salt['mc_apache.settings']().packages %}
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
      - version
      - rewrite
      - expires
      - headers
      - deflate
      - status
    - require_in:
      - mc_apache: makina-apache-main-conf
    - watch_in:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-pre-restart

makina-apache-main-conf-excluded-modules:
  mc_apache.exclude_module:
    - modules:
{% if not salt['mc_apache.settings']().allow_bad_modules.negotiation %}
      - negotiation
{% endif %}
{% if not salt['mc_apache.settings']().allow_bad_modules.autoindex %}
      - autoindex
{% endif %}
{% if not salt['mc_apache.settings']().allow_bad_modules.cgid %}
      - cgid
{% endif %}
    - require_in:
      - mc_apache: makina-apache-main-conf
    - watch_in:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-pre-restart
{# Read states documentation to alter main apache
# configuration
#}
makina-apache-main-conf:
  mc_apache.deployed:
    - version: {{ salt['mc_apache.settings']().version }}
    - mpm: {{ salt['mc_apache.settings']().mpm }}
    - log_level: {{ salt['mc_apache.settings']().log_level }}
    - watch:
      - mc_proxy: makina-apache-pre-conf
    # full service restart in case of changes
    - watch_in:
      # NO: this would prevent syntax check in case of error here
      # and errors here may be caused by syntax problems
      # - cmd: makina-apache-conf-syntax-check
      - mc_proxy: makina-apache-post-conf
      - mc_proxy: makina-apache-pre-restart

makina-apache-settings:
  file.managed:
    - name: {{ salt['mc_apache.settings']().confdir }}/settings.local.conf
    - source: salt://makina-states/files/etc/apache2/conf.d/settings.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
        mode: "production"
        Timeout: "{{ salt['mc_apache.settings']().Timeout }}"
        KeepAlive: "{{ salt['mc_apache.settings']().KeepAlive }}"
        MaxKeepAliveRequests: "{{ salt['mc_apache.settings']().MaxKeepAliveRequests }}"
        KeepAliveTimeout: "{{ salt['mc_apache.settings']().KeepAliveTimeout }}"
        prefork_StartServers: "{{ salt['mc_apache.settings']().prefork.StartServers }}"
        prefork_MinSpareServers: "{{ salt['mc_apache.settings']().prefork.MinSpareServers }}"
        prefork_MaxSpareServers: "{{ salt['mc_apache.settings']().prefork.MaxSpareServers }}"
        prefork_MaxClients: "{{ salt['mc_apache.settings']().prefork.MaxClients }}"
        prefork_MaxRequestsPerChild: "{{ salt['mc_apache.settings']().prefork.MaxRequestsPerChild }}"
        worker_StartServers: "{{ salt['mc_apache.settings']().worker.StartServers }}"
        worker_MinSpareThreads: "{{ salt['mc_apache.settings']().worker.MinSpareThreads }}"
        worker_MaxSpareThreads: "{{ salt['mc_apache.settings']().worker.MaxSpareThreads }}"
        worker_ThreadLimit: "{{ salt['mc_apache.settings']().worker.ThreadLimit }}"
        worker_ThreadsPerChild: "{{ salt['mc_apache.settings']().worker.ThreadsPerChild }}"
        worker_MaxRequestsPerChild: "{{ salt['mc_apache.settings']().worker.MaxRequestsPerChild }}"
        worker_MaxClients: "{{ salt['mc_apache.settings']().worker.MaxClients }}"
        event_AsyncRequestWorkerFactor: "{{ salt['mc_apache.settings']().event.AsyncRequestWorkerFactor }}"
        log_level: "{{ salt['mc_apache.settings']().log_level }}"
{% if salt['mc_nodetypes.registry']()['is']['devhost'] %}
    - context:
        mode: "dev"
{% endif %}
    - watch:
      - mc_proxy: makina-apache-post-inst
    # full service restart in case of changes
    - watch_in:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-pre-restart


makina-apache-mod-status-settings:
  file.managed:
    - name: {{ salt['mc_apache.settings']().confdir }}/mods-available/status.conf
    - source: salt://makina-states/files/etc/apache2/mods-available/status.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
        mode: "production"
        MonitoringServers: "{{ salt['mc_apache.settings']().monitoring.allowed_servers }}"
        ExtendedStatus: "{{ salt['mc_apache.settings']().monitoring.extended_status }}"
{% if salt['mc_nodetypes.registry']()['is']['devhost'] %}
    - context:
        mode: "dev"
{% endif %}
    - watch:
      - mc_proxy: makina-apache-post-inst
    # gracefull reload in case of changes
    - watch_in:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-pre-reload

{# Exemple to add a slug directly in apache configuration #}
makina-apache-main-extra-settings-example:
  file.accumulated:
    - name: extra-settings-master-conf
    - filename: {{ salt['mc_apache.settings']().confdir }}/settings.local.conf
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
    - name: {{ salt['mc_apache.settings']().confdir }}/_security.local.conf
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
#       - mc_proxy: makina-apache-pre-restart
#
# Exemple: add negociation in excluded modules
# WARNING: removing modules listed in makina-apache-main-conf-excluded-modules
# should be done on the defaults dictionnary
#makina-apache-other-module-excluded:
#  mc_apache.exclude_module:
#    - modules:
#      - negotiation
#    - watch_in:
#      - mc_apache: makina-apache-main-conf
#
#
#}

{% if full %}
# Directories settings -----------------
makina-apache-include-directory:
  file.directory:
    - user: root
    - group: {{salt['mc_apache.settings']().httpd_user}}
    - mode: "2755"
    - makedirs: True
    - name: {{ salt['mc_apache.settings']().basedir }}/includes
    - watch:
       - mc_proxy: makina-apache-post-inst
    - watch_in:
       - mc_proxy: makina-apache-pre-conf
       - mc_proxy: makina-apache-pre-restart

{# cronolog usage in {{ locs.var_dir }}/log/apache watchs a group write
# right which may not be present.
# we connect to restart as a reload wont be enough
#}
makina-apache-default-log-directory:
  file.directory:
    - user: root
    - group: {{salt['mc_apache.settings']().httpd_user}}
    - mode: "2770"
    - name: {{ salt['mc_apache.settings']().logdir }}
    - watch:
       - mc_proxy: makina-apache-post-inst
    - watch_in:
       - mc_proxy: makina-apache-pre-conf
       - mc_proxy: makina-apache-pre-restart

# Default Virtualhost managment -------------------------------------
{# Replace defaut Virtualhost by a more minimal default Virtualhost [1]
# this is the directory
#}
makina-apache-default-vhost-directory:
  file.directory:
    - user: root
    - group: {{salt['mc_apache.settings']().httpd_user}}
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
{% if salt['mc_nodetypes.registry']()['is']['devhost'] %}
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

{% endif %}
{# Replace defaut Virtualhost by a more minimal default Virtualhost [4]
# this is the virtualhost definition
#}
{% if full %}
makina-apache-minimal-default-vhost-remove-olds:
  file.absent:
    - names:
      - {{ salt['mc_apache.settings']().evhostdir }}/default
      - {{ salt['mc_apache.settings']().evhostdir }}/default-ssl
      - {{ salt['mc_apache.settings']().vhostdir }}/default
      - {{ salt['mc_apache.settings']().vhostdir }}/default-ssl
    - watch_in:
      - mc_proxy: makina-apache-post-inst
    - watch_in:
      - mc_proxy: makina-apache-pre-conf

{{apacheSettings.httpd_user}}-in-editor-group:
  user.present:
    - name: {{salt['mc_apache.settings']().httpd_user}}
    - system: true
    - remove_groups: False
    - groups:
      - {{localsettings.group}}
    - watch_in:
      - mc_proxy: makina-apache-pre-restart
{% endif %}
{#--- Configuration Check --------------------------------
# Configuration checker, always run before restart of graceful restart
#}
makina-apache-conf-syntax-check:
  cmd.script:
    - source: {{ apacheConfCheck }}
    - stateful: True
    - watch:
      - mc_proxy: makina-apache-post-conf
    - watch_in:
      - mc_proxy: makina-apache-pre-restart
      - mc_proxy: makina-apache-pre-reload

{#--- MAIN SERVICE RESTART/RELOAD watchers -------------- #}
makina-apache-restart:
  service.running:
    - name: {{ salt['mc_apache.settings']().service }}
    - enable: True
    # most watch requisites are linked here with watch_in
    - watch_in:
      - mc_proxy: makina-apache-post-restart
      # restart service in case of package install
    - watch:
      - mc_proxy: makina-apache-post-inst
      - mc_proxy: makina-apache-pre-restart

{# In case of VirtualHosts change graceful reloads should be enough
#}
makina-apache-reload:
  service.running:
    - name: {{ salt['mc_apache.settings']().service }}
    - watch_in:
      - mc_proxy: makina-apache-post-reload
    - watch:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-post-conf
      - mc_proxy: makina-apache-pre-reload
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
{% if 'virtualhosts' in salt['mc_apache.settings']() -%}
{%   for site, siteDef in salt['mc_apache.settings']()['virtualhosts'].items() -%}
{%     do siteDef.update({'domain': site}) %}
{{     apache.virtualhost(**siteDef) }}
{%-   endfor %}
{%- endif %}
{% endmacro %}
{{ do(full=False) }}

{# REMOVED, devhost is not using NFS anymore
#--- APACHE STARTUP WAIT DEPENDENCY --------------
{% if salt['mc_nodetypes.registry']()['is']['devhost'] %}
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
