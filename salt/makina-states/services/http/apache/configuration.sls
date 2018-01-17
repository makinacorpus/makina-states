{#
# To register new vhosts, use the virtualhost macros inside the macros found in this folder
#
# Extra module additions and removal
# Theses (valid) examples show you how
# to alter the modules_excluded and
# modules_included lists
#
# Exemple: add 3 modules
#
# makina-apache-other-module-included:
#   mc_apache.include_module:
#     - modules:
#       - deflate
#       - status
#       - cgid
#     - watch_in:
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
# Only one apache settings section is allowed
# Exemple of error: using a second mc_apache.deployed would fail
# as only one main apache configuration can be defined
# per server
# Use ``extend`` on makina-apache-main-conf instead
# makina-apache-main-conf2:
#   mc_apache.deployed:
#     - version: 2.2
#     - log_level: warn
#     - watch:
#       - mc_proxy: makina-apache-post-inst
#
# TODO: SSL VH
# TODO: detect invalid links in sites-enabled and remove them
# apache 2.4: EnableSendfile On, NameVirtualHost deprecated,  RewriteLog and RewriteLogLevel-> LogLevel rewrite:debug
# enable and configure mod_reqtimeout
#}
include:
  - makina-states.services.http.apache.hooks
  - makina-states.services.http.apache.services
  - makina-states.services.http.apache.vhosts

{% import "makina-states/services/http/apache/macros.sls" as macros with context %}
{% set nodetypes_registry = salt['mc_nodetypes.registry']() %}
{% set ugs = salt['mc_usergroup.settings']() %}
{% set locs = salt['mc_locations.settings']() %}
{% set apacheSettings = salt['mc_apache.settings']() %}
{% set old_mode = (grains['lsb_distrib_id']=="Ubuntu"
                    and grains['lsb_distrib_release']<13.10)
                    or (grains['lsb_distrib_id']=="Debian"
                        and grains['lsb_distrib_release']<=7.0) %}
{% set extend_switch_mpm = macros.extend_switch_mpm %}
{% set default_vh_template_source = macros.default_vh_template_source %}
{% set default_vh_in_template_source = macros.default_vh_in_template_source %}
{% set minimal_index = macros.minimal_index %}
{% set virtualhost = macros.virtualhost %}

# left over for retrocompat !
makina-apache-main-conf:
  mc_apache.deployed:
    - watch:
      - mc_proxy: makina-apache-pre-conf
    - watch_in:
      - mc_proxy: makina-apache-post-conf
      - mc_proxy: makina-apache-pre-restart

makina-apache-settings:
  file.managed:
    - name: {{ apacheSettings.confdir }}/settings.local.conf
    - source: salt://makina-states/files/etc/apache2/conf.d/settings.conf
    - user: root
    - group: root
    - mode: 644
    - makedirs: true
    - template: jinja
    - defaults:
        mode: "production"
        Timeout: "{{ apacheSettings.Timeout }}"
        KeepAlive: "{{ apacheSettings.KeepAlive }}"
        MaxKeepAliveRequests: "{{ apacheSettings.MaxKeepAliveRequests }}"
        KeepAliveTimeout: "{{ apacheSettings.KeepAliveTimeout }}"
        prefork_StartServers: "{{ apacheSettings.prefork.StartServers }}"
        prefork_MinSpareServers: "{{ apacheSettings.prefork.MinSpareServers }}"
        prefork_MaxSpareServers: "{{ apacheSettings.prefork.MaxSpareServers }}"
        prefork_MaxClients: "{{ apacheSettings.prefork.MaxClients }}"
        prefork_MaxRequestsPerChild: "{{ apacheSettings.prefork.MaxRequestsPerChild }}"
        worker_StartServers: "{{ apacheSettings.worker.StartServers }}"
        worker_MinSpareThreads: "{{ apacheSettings.worker.MinSpareThreads }}"
        worker_MaxSpareThreads: "{{ apacheSettings.worker.MaxSpareThreads }}"
        worker_ThreadLimit: "{{ apacheSettings.worker.ThreadLimit }}"
        worker_ThreadsPerChild: "{{ apacheSettings.worker.ThreadsPerChild }}"
        worker_MaxRequestsPerChild: "{{ apacheSettings.worker.MaxRequestsPerChild }}"
        worker_MaxClients: "{{ apacheSettings.worker.MaxClients }}"
        event_AsyncRequestWorkerFactor: "{{ apacheSettings.event.AsyncRequestWorkerFactor }}"
        log_level: "{{ apacheSettings.log_level }}"
        ssl_session_cache: "{{ apacheSettings.ssl_session_cache }}"
{% if salt['mc_nodetypes.is_devhost']() %}
    - context:
        mode: "dev"
{% endif %}
    - watch:
      - mc_proxy: makina-apache-post-inst
    # full service restart in case of changes
    - watch_in:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-pre-restart


{# Default lists of included and excluded modules
 extend theses two states if you need others modules #}
makina-apache-main-conf-excluded-modules:
  mc_apache.exclude_module:
    - modules:
      {% for i in apacheSettings.exclude_modules %}
      - {{i}}
      {% endfor %}
    - watch:
      - mc_proxy: makina-apache-post-inst
    # full service restart in case of changes
    - watch_in:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-pre-restart

makina-apache-main-conf-included-modules:
  mc_apache.include_module:
    - modules:
      {% for i in apacheSettings.include_modules %}
      - {{i}}
      {% endfor %}
    - watch:
      - mc_proxy: makina-apache-post-inst
    # full service restart in case of changes
    - watch_in:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-pre-restart

{{apacheSettings.httpd_user}}-in-editor-group:
  user.present:
    - name: {{apacheSettings.httpd_user}}
    - system: true
    - remove_groups: False
    - groups:
      - {{ugs.group}}
    - watch_in:
      - mc_proxy: makina-apache-pre-restart

# Directories settings -----------------
makina-apache-include-directory:
  file.directory:
    - user: root
    - group: {{apacheSettings.httpd_user}}
    - mode: "2755"
    - makedirs: True
    - name: {{ apacheSettings.basedir }}/includes
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
    - group: {{apacheSettings.httpd_user}}
    - mode: "2770"
    - name: {{ apacheSettings.logdir }}
    - watch:
       - mc_proxy: makina-apache-post-inst
    - watch_in:
       - mc_proxy: makina-apache-pre-conf
       - mc_proxy: makina-apache-pre-restart


{# Define some basic security restrictions, like forbidden acces to all
# directories by default, switch off signatures protect .git, etc
# file is named _security to be read after the default security file
# in conf.d directory
#}
makina-apache-security-settings:
  file.managed:
    - watch:
      - mc_proxy: makina-apache-post-inst
    - name: {{ apacheSettings.confdir }}/_security.local.conf
    - makedirs: true
    - source:
      - salt://makina-states/files/etc/apache2/conf.d/security.conf
    - user: root
    - group: root
    - mode: 644
    - watch:
       - mc_proxy: makina-apache-post-inst
    - watch_in:
       - mc_proxy: makina-apache-pre-conf

{# Exemple to add a slug directly in apache configuration #}
makina-apache-main-extra-settings-example:
  file.accumulated:
    - name: extra-settings-master-conf
    - filename: {{ apacheSettings.confdir }}/settings.local.conf
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

makina-apache-fix-log:
  file.absent:
    - names:
      - /etc/apache2/conf-enabled/other-vhosts-access-log.conf
    - watch:
       - mc_proxy: makina-apache-post-inst
    - watch_in:
       - mc_proxy: makina-apache-pre-conf

makina-apache-mod-status-settings:
  file.managed:
    - name: {{ apacheSettings.confdir }}/mods-available/status.conf
    - source: salt://makina-states/files/etc/apache2/mods-available/status.conf
    - user: root
    - group: root
    - mode: 644
    - makedirs: true
    - template: jinja
    - defaults:
        mode: "production"
        MonitoringServers: "{{ apacheSettings.monitoring.allowed_servers }}"
        ExtendedStatus: "{{ apacheSettings.monitoring.extended_status }}"
{% if salt['mc_nodetypes.is_devhost']() %}
    - context:
        mode: "dev"
{% endif %}
    - watch:
      - mc_proxy: makina-apache-post-inst
    # gracefull reload in case of changes
    - watch_in:
      - mc_proxy: makina-apache-pre-conf
      - mc_proxy: makina-apache-pre-reload
