# Apache httpd managment
#
# Makina Corpus Apache Deployment main state
#
# Preferred way of altering default settings is to extend the states
# makina-apache-main-conf and makina-apache-settings this way:
#------------ state exemple --------------------------------
## remember theses 4 rules for extend:
##1-Always include the SLS being extended with an include declaration
##2-Requisites (watch and require) are appended to, everything else is overwritten
##3-extend is a top level declaration, like an ID declaration, cannot be declared twice in a single SLS
##4-Many IDs can be extended under the extend declaration
#
#include:
#  - makina-states.services.http.apache
#extend:
#  makina-apache-main-conf:
#    mc_apache:
#      - version: 2.4
#      - mpm: worker
#  makina-apache-settings:
#    file:
#      - context:
#        KeepAliveTimeout: 3
#        worker_StartServers: "5"
#        worker_MinSpareThreads: "60"
#        worker_MaxSpareThreads: "120"
#        worker_ThreadLimit: "120"
#        worker_ThreadsPerChild: "60"
#        worker_MaxRequestsPerChild: "1000"
#        worker_MaxClients: "500"
#
## Adding or removing modules
#my-apache-other-module-included1:
#  mc_apache.include_module:
#    - modules:
#      - proxy_http
#      - proxy_html
#    - require_in:
#      - mc_apache: makina-apache-main-conf
# Adding or removing modules
#my-apache-other-module-included2:
#  mc_apache.include_module:
#    - modules:
#      - authn_file
#    - require_in:
#      - mc_apache: makina-apache-main-conf
#my-apache-other-module--other-module-excluded:
#  mc_apache.exclude_module:
#    - modules:
#      - rewrite
#    - require_in:
#      - mc_apache: makina-apache-main-conf
#------------ end of state exemple ------------------------------
#
# But configuration can also be made in the pillar, to alter
# default values without using states
#
# ------------------------- START pillar example -----------
#
# --- APACHE HTTPD SERVER
#
# - LOGS ------------------
# default: warn
# available: debug, info, notice, warn, error, crit, alert, emerg
#services-http-apache-log_level: info
#
# - SETTINGS ------------------
# TODO: review
#services-http-apache-serveradmin_mail : 'webmaster@localhost'
# timeout for a client sending HTTP request, keep this quite low to avoid DOS
#services-http-apache-Timeout: 120
# default is 'On', you can use 'Off', especially in mpm mode
#services-http-apache-KeepAlive: 'On'
# Please keep this one under 5s, default is "5"
#services-http-apache-KeepAliveTimeout: 5
# default for theses 3 is 5 in dev mode, 25 else.
#services-http-apache-prefork_StartServers: 5
#services-http-apache-prefork_MinSpareServers: 5
#services-http-apache-prefork_MaxSpareServers: 5
# default is 150 or 10 in dev mode
#services-http-apache-prefork_MaxClients: 10
# default is 100 or 5 in dev mode
#services-http-apache-MaxKeepAliveRequests: 5
# default is 3000 set 0 to disable process recylcing
#services-http-apache-MaxRequestsPerChild: 3000
# Put there any configuration directive for the main apache scope, you can use \n.
#services-http-apache-extra_configuration : 'ServerLimit 1000'
#
# do not forget to launch "salt '*' saltutil.refresh_pillar" after changes 
# ------------------------- END pillar example -------------
#
# consult pillar values with "salt '*' pillar.items"
# consult grains values with "salt '*' grains.items"
#
# TODO: alter mod_status conf to allow only localhost,monitoring some user defined IP,  ExtendedStatus Off
# TODO: Vhost states
# TODO: SSL, ports, and default-ssl


{% set msr='/srv/salt/makina-states' %}
{% set apacheConfCheck = "file://"+msr+"/_scripts/apacheConfCheck.sh" %}
# Load defaults values -----------------------------------------
{% set dft_log_level = salt['pillar.get']('services-http-apache-log_level', 'warn') %}
{% set dft_Timeout = salt['pillar.get']('services-http-apache-Timeout', '120') %}
{% set dft_KeepAlive = salt['pillar.get']('services-http-apache-KeepAlive', 'On') %}
{% set dft_KeepAliveTimeout = salt['pillar.get']('services-http-apache-KeepAliveTimeout', '5') %}
{% set dft_extra_configuration = salt['pillar.get']('services-http-apache-extra_configuration', '#') %}
{% set dft_serveradmin_mail = salt['pillar.get']('services-http-apache-serveradmin_mail', 'webmaster@localhost') %}
{% if grains['makina.devhost'] %}
  {% set dft_MaxKeepAliveRequests = salt['pillar.get']('services-http-apache-MaxKeepAliveRequests', '5') %}
  # mpm prefork
  # StartServers: number of server processes to start
  {% set dft_prefork_StartServers = salt['pillar.get']('services-http-apache-prefork_StartServers', '5') %}
  # MinSpareServers: minimum number of server processes which are kept spare
  {% set dft_prefork_MinSpareServers = salt['pillar.get']('services-http-apache-prefork_MinSpareServers', '5') %}
  # MaxSpareServers: maximum number of server processes which are kept spare
  {% set dft_prefork_MaxSpareServers = salt['pillar.get']('services-http-apache-prefork_MaxSpareServers', '5') %}
  # MaxRequestWorkers (alias MaxClients): maximum number of server processes allowed to start
  {% set dft_prefork_MaxClients = salt['pillar.get']('services-http-apache-prefork_MaxClients', '10') %}
  # MaxConnectionsPerChild: maximum number of requests a server process serves
  {% set dft_prefork_MaxRequestsPerChild = salt['pillar.get']('services-http-apache-prefork_MaxRequestsPerChild', '3000') %}
  # mpm worker
  # StartServers: initial number of server processes to start
  {% set dft_worker_StartServers = salt['pillar.get']('services-http-apache-worker_StartServers', '2') %}
  # MinSpareThreads: minimum number of worker threads which are kept spare
  {% set dft_worker_MinSpareThreads = salt['pillar.get']('services-http-apache-worker_MinSpareThreads', '25') %}
  # MaxSpareThreads: maximum number of worker threads which are kept spare
  {% set dft_worker_MaxSpareThreads = salt['pillar.get']('services-http-apache-worker_MaxSpareThreads', '75') %}
  # ThreadLimit: ThreadsPerChild can be changed to this maximum value during a
  #             graceful restart. ThreadLimit can only be changed by stopping
  #             and starting Apache.
  {% set dft_worker_ThreadLimit = salt['pillar.get']('services-http-apache-worker_ThreadLimit', '64') %}
  # ThreadsPerChild: constant number of worker threads in each server process
  {% set dft_worker_ThreadsPerChild = salt['pillar.get']('services-http-apache-worker_ThreadsPerChild', '25') %}
  # MaxRequestsPerChild/MaxConnectionsPerChild: maximum number of requests a server process serves
  {% set dft_worker_MaxRequestsPerChild = salt['pillar.get']('services-http-apache-worker_MaxRequestsPerChild', '0') %}
  # MaxRequestWorkers (alias MaxClients): maximum number of threads
  {% set dft_worker_MaxClients = salt['pillar.get']('services-http-apache-worker_MaxClients', '10') %}
  # mpm event
  # all workers settings are used
  # max of concurrent conn is (AsyncRequestWorkerFactor + 1) * MaxRequestWorkers
  {% set dft_event_AsyncRequestWorkerFactor = salt['pillar.get']('services-http-apache-event_AsyncRequestWorkerFactor', '1.5') %}

{% else %}
  {% set dft_MaxKeepAliveRequests = salt['pillar.get']('services-http-apache-MaxKeepAliveRequests', '100') %}
  {% set dft_prefork_StartServers = salt['pillar.get']('services-http-apache-prefork_StartServers', '25') %}
  {% set dft_prefork_MinSpareServers = salt['pillar.get']('services-http-apache-prefork_MinSpareServers', '25') %}
  {% set dft_prefork_MaxSpareServers = salt['pillar.get']('services-http-apache-prefork_MaxSpareServers', '25') %}
  {% set dft_prefork_MaxClients = salt['pillar.get']('services-http-apache-prefork_MaxClients', '150') %}
  {% set dft_prefork_MaxRequestsPerChild = salt['pillar.get']('services-http-apache-prefork_MaxRequestsPerChild', '3000') %}
  {% set dft_worker_StartServers = salt['pillar.get']('services-http-apache-worker_StartServers', '5') %}
  {% set dft_worker_MinSpareThreads = salt['pillar.get']('services-http-apache-worker_MinSpareThreads', '50') %}
  {% set dft_worker_MaxSpareThreads = salt['pillar.get']('services-http-apache-worker_MaxSpareThreads', '100') %}
  {% set dft_worker_ThreadLimit = salt['pillar.get']('services-http-apache-worker_ThreadLimit', '100') %}
  {% set dft_worker_ThreadsPerChild = salt['pillar.get']('services-http-apache-worker_ThreadsPerChild', '50') %}
  {% set dft_worker_MaxRequestsPerChild = salt['pillar.get']('services-http-apache-worker_MaxRequestsPerChild', '3000') %}
  {% set dft_worker_MaxClients = salt['pillar.get']('services-http-apache-worker_MaxClients', '200') %}
  {% set dft_event_AsyncRequestWorkerFactor = salt['pillar.get']('services-http-apache-event_AsyncRequestWorkerFactor', '4') %}
{% endif %}
{% if grains['lsb_distrib_id']=="Ubuntu" and grains['lsb_distrib_release']>=13.10 %}
  {% set dft_mpm = salt['pillar.get']('services-http-apache-mpm', 'event') %}
  {% set dft_version = salt['pillar.get']('services-http-apache-version', '2.4') %}
{% else %}
  {% set dft_mpm = salt['pillar.get']('services-http-apache-mpm', 'worker') %}
  {% set dft_version = salt['pillar.get']('services-http-apache-version', '2.2') %}
{% endif %}

makina-apache-pkgs:
  pkg.installed:
    - pkgs:
      - apache2
      - cronolog

# Apache Main Configuration ------------------
# Read states documentation to alter main apache
# configuration
makina-apache-main-conf:
  mc_apache.deployed:
    - version: {{ dft_version }}
    - mpm: {{ dft_mpm }}
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
    - log_level: {{ dft_log_level }}
    - require:
      - pkg.installed: makina-apache-pkgs
    # full service restart in case of changes
    - watch_in:
       - cmd: makina-apache-conf-syntax-check
       - service: makina-apache-restart

makina-apache-settings:
  file.managed:
    - name: /etc/apache2/conf.d/settings.local.conf
    - source: salt://makina-states/files/etc/apache2/conf.d/settings.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
        mode: "production"
        Timeout: "{{ dft_Timeout }}"
        KeepAlive: "{{ dft_KeepAlive }}"
        MaxKeepAliveRequests: "{{ dft_MaxKeepAliveRequests }}"
        KeepAliveTimeout: "{{ dft_KeepAliveTimeout }}"
        prefork_StartServers: "{{ dft_prefork_StartServers }}"
        prefork_MinSpareServers: "{{ dft_prefork_MinSpareServers }}"
        prefork_MaxSpareServers: "{{ dft_prefork_MaxSpareServers }}"
        prefork_MaxClients: "{{ dft_prefork_MaxClients }}"
        prefork_MaxRequestsPerChild: "{{ dft_prefork_MaxRequestsPerChild }}"
        worker_StartServers: "{{ dft_worker_StartServers }}"
        worker_MinSpareThreads: "{{ dft_worker_MinSpareThreads }}"
        worker_MaxSpareThreads: "{{ dft_worker_MaxSpareThreads }}"
        worker_ThreadLimit: "{{ dft_worker_ThreadLimit }}"
        worker_ThreadsPerChild: "{{ dft_worker_ThreadsPerChild }}"
        worker_MaxRequestsPerChild: "{{ dft_worker_MaxRequestsPerChild }}"
        worker_MaxClients: "{{ dft_worker_MaxClients }}"
        event_AsyncRequestWorkerFactor: "{{ dft_event_AsyncRequestWorkerFactor }}"
        log_level: "{{ dft_log_level }}"
        extra_configuration: "{{ dft_extra_configuration }}"
{% if grains['makina.devhost'] %}
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
    - filename: /etc/apache2/conf.d/settings.local.conf
    - text: |
        '# this is an example of thing added in master apache configuration'
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
    - name: /etc/apache2/conf.d/_security.local.conf
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
#      - pkg.installed: makina-apache-pkgs



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
    - name: /etc/apache2/includes
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
    - name: /var/log/apache2
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
       - pkg.installed: makina-apache-pkgs
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
{% if grains['makina.devhost'] %}
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
      - pkg.installed: makina-apache-pkgs
      - file.managed: makina-apache-default-vhost-index
{% if grains['lsb_distrib_id']=="Ubuntu" and grains['lsb_distrib_release']>=13.10 %}
    - name: /etc/apache2/sites-available/000-default.conf
{% else %}
    - name: /etc/apache2/sites-available/default
{% endif %}
    - source:
      - salt://makina-states/files/etc/apache2/sites-available/default_vh.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
        log_level: "{{ dft_log_level }}"
        serveradmin_mail: "{{ dft_serveradmin_mail }}"
        mode: "production"
{% if grains['makina.devhost'] %}
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
      - pkg.installed: makina-apache-pkgs
    - require_in:
       - service: makina-apache-restart
       - service: makina-apache-reload

#--- MAIN SERVICE RESTART/RELOAD watchers --------------

makina-apache-restart:
  service.running:
    - name: apache2
    - enable: True
    # most watch requisites are linked here with watch_in
    - watch:
      # restart service in case of package install
      - pkg.installed: makina-apache-pkgs

# In case of VirtualHosts change graceful reloads should be enough
makina-apache-reload:
  service.running:
    - name: apache2
    - require:
      - pkg.installed: makina-apache-pkgs
    - enable: True
    - reload: True
    # most watch requisites are linked here with watch_in



# Virtualhost example: work in progress----------------
{% set site_enabled = True %}
makina-apache-virtualhost-example_com:
  file.managed:
    - user: root
    - group: root
    - mode: 664
{% if grains['lsb_distrib_id']=="Ubuntu" and grains['lsb_distrib_release']>=13.10 %}
    - name: /etc/apache2/sites-available/200-example.com.conf
{% else %}
    - name: /etc/apache2/sites-available/200-example.com
{% endif %}
    - source:
        - salt://makina-states/files/etc/apache2/sites-available/virtualhost_template.conf
    - template: 'jinja'
    - defaults:
        log_level: "{{ dft_log_level }}"
        serveradmin_mail: "{{ dft_serveradmin_mail }}"
        # used in log file name for example
        site_small_name: "example"
        DocumentRoot: "/srv/projects/foo/www/example.com"
        ServerName: "example.com"
        ServerAlias: 
          - "www.example.com"
          - "www1.example.com"
          - "www2.example.com"
          - "www3.example.com"
        redirect_aliases: True
        interface: "*"
        port: "80"
        mode: "production"
{% if grains['makina.devhost'] %}
    - context:
        mode: "dev"
{% endif %}
    - require:
      - pkg.installed: makina-apache-pkgs
    - watch_in:
      - cmd: makina-apache-virtualhost-example_com-status
      - cmd: makina-apache-conf-syntax-check
      - service: makina-apache-reload

makina-apache-virtualhost-example_com-content:
  file.managed:
    - user: root
    - group: root
    - mode: 664
    - name: /etc/apache2/includes/example.com.conf
    - source:
        - salt://makina-states/files/etc/apache2/includes/in_virtualhost_template.conf
    - template: 'jinja'
    - defaults:
        DocumentRoot: "/srv/projects/foo/www/example.com"
        mode: "production"
        allow_htaccess: False
{% if grains['makina.devhost'] %}
    - context:
        mode: "dev"
{% endif %}
    - require:
      - pkg: makina-apache-pkgs
      - file: makina-apache-include-directory
    - require_in:
      - file: makina-apache-virtualhost-example_com
    - watch_in:
      - cmd: makina-apache-conf-syntax-check
      - service: makina-apache-reload


makina-apache-virtualhost-example_com-status:
  cmd.run:
{% if site_enabled %}
    - name: a2ensite 200-example.com
{% if grains['lsb_distrib_id']=="Ubuntu" and grains['lsb_distrib_release']>=13.10 %}
    - unless: ls /etc/apache2/sites-enabled/200-example.com.conf
{% else %}
    - unless: ls /etc/apache2/sites-enabled/200-example.com
{% endif %}
{% else %}
    - name: a2dissite 200-example.com
{% if grains['lsb_distrib_id']=="Ubuntu" and grains['lsb_distrib_release']>=13.10 %}
    - onlyif: ls /etc/apache2/sites-enabled/200-example.com.conf
{% else %}
    - onlyif: ls /etc/apache2/sites-enabled/200-example.com
{% endif %}
{% endif %}
    - require:
      - pkg: makina-apache-pkgs
    - watch_in:
      - cmd: makina-apache-conf-syntax-check
      - service: makina-apache-reload
