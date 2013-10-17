# define in pillar an apache default loglevel :
#   apache.log_level: debug
#   apache.disabled_modules: 'autoindex cgid negotiation'
# default is warn, 
# available values are: debug, info, notice, warn, error, crit, alert, emerg
# @see apache documentation for LogLevel
{% set log_level = pillar.get('apache.log_level', 'warn') %}
{% set disabled_modules = pillar.get('apache.disabled_modules', 'autoindex cgid negotiation') %}
{% set enabled_modules = pillar.get('apache.enabled_modules', 'deflate status expires headers rewrite') %}
#
# 
#
{% set msr='/srv/salt/makina-states' %}
{% set a2dismodwrapper = "file://"+msr+"/_scripts/a2dismodwrapper.sh" %}
{% set a2enmodwrapper = "file://"+msr+"/_scripts/a2enmodwrapper.sh" %}




apache-pkgs:
  pkg.installed:
    - names:
      - apache2
      - cronolog

# Define some basic security restrictions, like forbidden acces to all
# dorectories by default, switch off signatures protect .git, etc
# file is name _security to be read after the default security file
apache-security-settings:
  file.managed:
    - require:
      - pkg.installed: apache-pkgs
    - name: /etc/apache2/conf.d/_security
    - source:
      - salt://makina-states/files/etc/apache2/conf.d/security.conf
    - user: root
    - group: root
    - mode: 644

# Replace defaut Virtualhost by a more minmal default Virtualhost
# this is the directory
apache-default-vhost-directory:
  file.directory:
    - user: root
    - group: www-data
    - mode: "2755"
    - makedirs: True
    - name: /var/www/default/

# Replace defaut Virtualhost by a more minmal default Virtualhost
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
  
# Replace defaut Virtualhost by a more minmal default Virtualhost
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

makina-apache-service:
  service.running:
    - name: apache2
    - require:
      - pkg.installed: apache-pkgs
      - file.managed: apache-security-settings
      - file.managed: apache-minimal-default-vhost
    - watch:
      # reload service in case of package install
      - pkg.installed: apache-pkgs
      # reload service in case ofdefault VH alteration
      - file.managed: apache-minimal-default-vhost
      # reload service in case of modules alterations
      - cmd: apache-disable-useless-modules
      - cmd: apache-enable-required-modules
