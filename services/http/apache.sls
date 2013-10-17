# Apache httpd managment
#
# ------------------------- START pillar example -----------
#services:
#  http:
#    # --- APACHE HTTPD SERVER -----------------------------
#    apache:
#      # - LOGS ------------------
#      # default: warn
#      # available: debug, info, notice, warn, error, crit, alert, emerg
#      log_level: info
#      # - MODULES ------------------
#      # DO NOT FORGET to re-add default disabled modules or re-disable default enabled modules
#      # in case of changes
#      # default is 'autoindex cgid negotiation'
#      disabled_modules: 'autoindex cgid negotiation'
#      # default is 'deflate status expires headers rewrite'
#      enabled_modules: 'deflate status expires headers rewrite'
#      # - SETTINGS ------------------
#      # bof
#      serveradmin_mail : 'webmaster@localhost'
#      # timeout for a client sending HTTP request, keep this quite low to avoid DOS
#      Timeout: 120
#      # default is 'On', you can use 'Off', especially in mpm mode
#      KeepAlive: 'On'
#      # Please keep this one under 5s, default is "5"
#      KeepAliveTimeout: 5
#      # default for theses 3 is 5 in dev mode, 25 else.
#      prefork_StartServers: 5
#      prefork_MinSpareServers: 5
#      prefork_MaxSpareServers: 5
#      # default is 150 or 10 in dev mode
#      prefork_MaxClients: 10
#      # default is 100 or 5 in dev mode
#      MaxKeepAliveRequests: 5
#      # default is 3000 set 0 to disable process recylcing
#      MaxRequestsPerChild: 3000
#      # Put there any configuration directive for the main apache scope, you can use \n.
#      extra_configuration : 'ServerLimit 1000'
# do not forget to launch "salt '*' saltutil.refresh_pillar" after changes 
# --------------------------- END pillar example ------------
#
{% set log_level = salt['pillar.get']('services:http:apache:log_level', 'warn') %}
{% set disabled_modules = salt['pillar.get']('services:http:apache:disabled_modules', 'autoindex cgid negotiation') %}
{% set enabled_modules = salt['pillar.get']('services:http:apache:enabled_modules', 'deflate status expires headers rewrite') %}
{% set Timeout = salt['pillar.get']('services:http:apache:Timeout', '120') %}
{% set KeepAlive = salt['pillar.get']('services:http:apache:KeepAlive', 'On') %}
{% set KeepAliveTimeout = salt['pillar.get']('services:http:apache:KeepAliveTimeout', '5') %}
{% set extra_configuration = salt['pillar.get']('services:http:apache:extra_configuration', '#') %}
{% set serveradmin_mail = salt['pillar.get']('services:http:apache:serveradmin_mail', 'webmaster@localhost') %}
{% if grains['makina.devhost'] %}
  {% set prefork_StartServers = salt['pillar.get']('services:http:apache:prefork_StartServers', '5') %}
  {% set prefork_MinSpareServers = salt['pillar.get']('services:http:apache:prefork_MinSpareServers', '5') %}
  {% set prefork_MaxSpareServers = salt['pillar.get']('services:http:apache:prefork_MaxSpareServers', '5') %}
  {% set prefork_MaxClients = salt['pillar.get']('services:http:apache:prefork_MaxClients', '10') %}
  {% set MaxRequestsPerChild = salt['pillar.get']('services:http:apache:MaxRequestsPerChild', '3000') %}
  {% set MaxKeepAliveRequests = salt['pillar.get']('services:http:apache:MaxKeepAliveRequests', '5') %}
{% else %}
  {% set prefork_StartServers = salt['pillar.get']('services:http:apache:prefork_StartServers', '25') %}
  {% set prefork_MinSpareServers = salt['pillar.get']('services:http:apache:prefork_MinSpareServers', '25') %}
  {% set prefork_MaxSpareServers = salt['pillar.get']('services:http:apache:prefork_MaxSpareServers', '25') %}
  {% set prefork_MaxClients = salt['pillar.get']('services:http:apache:prefork_MaxClients', '150') %}
  {% set MaxRequestsPerChild = salt['pillar.get']('services:http:apache:MaxRequestsPerChild', '3000') %}
  {% set MaxKeepAliveRequests = salt['pillar.get']('services:http:apache:MaxKeepAliveRequests', '100') %}
{% endif %}

{% set msr='/srv/salt/makina-states' %}
{% set a2dismodwrapper = "file://"+msr+"/_scripts/a2dismodwrapper.sh" %}
{% set a2enmodwrapper = "file://"+msr+"/_scripts/a2enmodwrapper.sh" %}
{% set apacheConfCheck = "file://"+msr+"/_scripts/apacheConfCheck.sh" %}

apache-pkgs:
  pkg.installed:
    - names:
      - apache2
      - cronolog

# Define some basic security restrictions, like forbidden acces to all
# directories by default, switch off signatures protect .git, etc
# file is named _security to be read after the default security file
# in conf.d directory
apache-security-settings:
  file.managed:
    - require:
      - pkg.installed: apache-pkgs
    - name: /etc/apache2/conf.d/_security.local.conf
    - source:
      - salt://makina-states/files/etc/apache2/conf.d/security.conf
    - user: root
    - group: root
    - mode: 644

# Define some basic tuning settings, like Timeouts, ports mpm settings,
# NamevirtualHost listeners, etc
# file is set in conf.d directory to override previous settings
# defined in the apache2.conf or ports.conf
apache-settings:
  file.managed:
    - require:
      - pkg.installed: apache-pkgs
    - name: /etc/apache2/conf.d/settings.local.conf
    - source:
      - salt://makina-states/files/etc/apache2/conf.d/settings.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
        mode: "production"
        Timeout: "{{Timeout}}"
        KeepAlive: "{{KeepAlive}}"
        MaxKeepAliveRequests: "{{MaxKeepAliveRequests}}"
        KeepAliveTimeout: "{{KeepAliveTimeout}}"
        prefork_StartServers: "{{prefork_StartServers}}"
        prefork_MinSpareServers: "{{prefork_MinSpareServers}}"
        prefork_MaxSpareServers: "{{prefork_MaxSpareServers}}"
        prefork_MaxClients: "{{prefork_MaxClients}}"
        MaxRequestsPerChild: "{{MaxRequestsPerChild}}"
        log_level: "{{log_level}}"
        extra_configuration: "{{extra_configuration}}"
{% if grains['makina.devhost'] %}
    - context:
        mode: "dev"
{% endif %}

# Replace defaut Virtualhost by a more minimal default Virtualhost
# this is the directory
apache-default-vhost-directory:
  file.directory:
    - user: root
    - group: www-data
    - mode: "2755"
    - makedirs: True
    - name: /var/www/default/

# Replace defaut Virtualhost by a more minimal default Virtualhost
# this is the index.hml file
apache-default-vhost-index:
  file.managed:
    - require:
      - pkg.installed: apache-pkgs
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

apache-remove-package-default-index:
  file.absent:
    - name : /var/www/index.hml
  
# Replace defaut Virtualhost by a more minimal default Virtualhost
# this is the virtualhost definition
apache-minimal-default-vhost:
  file.managed:
    - require:
      - pkg.installed: apache-pkgs
      - file.managed: apache-default-vhost-index
    - name: /etc/apache2/sites-available/default
    - source:
      - salt://makina-states/files/etc/apache2/sites-available/default_vh.conf
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - defaults:
        log_level: "{{log_level}}"
        serveradmin_mail: "{{serveradmin_mail}}"
        mode: "production"
{% if grains['makina.devhost'] %}
    - context:
        mode: "dev"
{% endif %}

# Enable/Disable Apache modules
# This is a cmd state. changed status will be assumed if command output is non-empty
apache-disable-useless-modules:
  cmd.script:
    - stateful: True
    - source: {{a2dismodwrapper}}
    - args: "{{disabled_modules}}"
    - require:
      - pkg.installed: apache-pkgs
apache-enable-required-modules:
  cmd.script:
    - stateful: True
    - source: {{a2enmodwrapper}}
    - args: "{{enabled_modules}}"
    - require:
      - pkg.installed: apache-pkgs

makina-apache-conf-syntax-check:
  cmd.script:
    - source: {{apacheConfCheck}}
    - stateful: True
    - require:
      - pkg.installed: apache-pkgs

#@see also makina-apache-service-graceful-reload
makina-apache-service:
  service.running:
    - name: apache2
    - enable: True
    - require:
      - pkg.installed: apache-pkgs
      - file.managed: apache-security-settings
      - file.managed: apache-minimal-default-vhost
      - cmd: makina-apache-conf-syntax-check
    - watch:
      # restart service in case of package install
      - pkg.installed: apache-pkgs
      # restart service in case of settings alterations
      - file.managed: apache-settings
      - file.managed: apache-security-settings
      # restart service in case of modules alterations
      - cmd: apache-disable-useless-modules
      - cmd: apache-enable-required-modules

# In case of VirtualHosts change graceful reloads should be enough
makina-apache-service-graceful-reload:
  service.running:
    - name: apache2
    - require:
      - pkg.installed: apache-pkgs
      - file.managed: apache-security-settings
      - file.managed: apache-minimal-default-vhost
      - cmd: makina-apache-conf-syntax-check
    - enable: True
    - reload: True
    - watch:
      # reload service in case of default VH alteration
      - file.managed: apache-minimal-default-vhost
