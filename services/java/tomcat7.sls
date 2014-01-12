# {#
#
# MANAGE A TOMCAT7 INSTALLATION VIA SALT.
# You can see in ./tomcat7-defaults.jinja the defaults associated with those states.
# By default, we will use the java6 oracle jdk jvm.
#
# You can override default settings in pillar via the 'tomcat7-default-settings' key:
#
# For example:
# tomcat7-default-settings:
#      java_home': /usr/lib/jvm/java-6-oracle
#  users:
#    admin:
#      password: {{ password }}
#      roles': ['admin', 'manager']
#
# AVAILABLE DEFAULT SETTINGS:
#   java_opts: java opts to give to tomcat start
#   java_home: JAVA_HOME of the jdk to use
#   users: mapping of users, roles & password:
#       {
#           'admin': {
#             'password': 'admin',
#             'roles': ['admin', 'manager'],
#           }
#       }
#   shutdown_port: default shutdown port (8005)
#   tomcat_user: tomcat system user
#   tomcat_group: tomcat system group
#   address: default address to listen on
#   port: default http port (8080)
#   ssl_port: default ssl port (8443)
#   ajp_port: default ajp port (8009)
#   defaultHost': default hostname (localhost)
#   welcome_files': list of files to serve as index (index.{htm,html,jsp})
#
# CUSTOM CONFIGURATION BLOCKS:
# Thanks to file.blockreplace + file.accumulated, you can also add on the fly raw tomcat configuration blocks.
# Custom configuration blocks have been wired on those files:
#   - server.xml
#   - context.xml
#   - web.xml
#   - logging.properties
#   - {{ locs.conf_dir }}/default/tomcat7 (practical to add JAVA_OPTS addition from other sls (eg adding solr datadir & home properties)
#   - catalina.properties
# See at the end of this state file for the appropriate blockreplace to use
# in your case and where those block are located in the aforementioned files.
# What you will need is just to make a file.accumulated requirin the appropriate
# file.blockreplace ID to add your configuration block.
#
# #}

{% import "makina-states/services/java/tomcat7-defaults.jinja" as tomcat with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{{ services.register('java.tomcat7') }}
{% set localsettings = services.localsettings %}
{% set locs = localsettings.locations %}
{% set conf_dir = tomcat.defaultsData['conf_dir'] %}
{% set ver = tomcat.defaultsData['ver'] %}
{% set data = tomcat.defaultsData %}

include:
  - {{ localsettings.statesPref }}jdk }}

tomcat-pkgs:
  pkg.installed:
    - pkgs:
      - tomcat{{ ver }}
    - require:
      - pkg: jdk-6-pkgs

{{ locs.conf_dir }}-default-tomcat{{ ver }}:
  file.managed:
    - name: {{ locs.conf_dir }}/default/tomcat{{ ver }}
    - source: salt://makina-states/files/etc/default/tomcat{{ ver }}
    - template: jinja
    - defaults: {{ tomcat.defaultsData | yaml }}

{{ conf_dir }}-web.xml:
  file.managed:
    - name: {{ conf_dir }}/web.xml
    - order: 100
    - source: salt://makina-states/files/{{ conf_dir }}/web.xml
    - template: jinja
    - defaults: {{ tomcat.defaultsData | yaml }}

{{ conf_dir }}-Catalina-localhost:
  file.directory:
    - name: {{ conf_dir }}/Catalina/localhost
    - makedirs: true

{{ conf_dir }}-tomcat-users.xml:
  file.managed:
    - name: {{ conf_dir }}/tomcat-users.xml
    - order: 100
    - source: salt://makina-states/files/{{ conf_dir }}/tomcat-users.xml
    - template: jinja
    - defaults: {{ tomcat.defaultsData | yaml }}

{{ conf_dir }}-logging.properties:
  file.managed:
    - name: {{ conf_dir }}/logging.properties
    - source: salt://makina-states/files/{{ conf_dir }}/logging.properties
    - order: 100
    - template: jinja
    - defaults: {{ tomcat.defaultsData | yaml }}

{{ conf_dir }}-policy.d-04webapps.policy:
  file.managed:
    - name: {{ conf_dir }}/policy.d/04webapps.policy
    - order: 100
    - source: salt://makina-states/files/{{ conf_dir }}/policy.d/04webapps.policy
    - template: jinja
    - defaults: {{ tomcat.defaultsData | yaml }}

{{ conf_dir }}-policy.d-02debian.policy:
  file.managed:
    - name: {{ conf_dir }}/policy.d/02debian.policy
    - order: 100
    - source: salt://makina-states/files/{{ conf_dir }}/policy.d/02debian.policy
    - template: jinja
    - defaults: {{ tomcat.defaultsData | yaml }}

{{ conf_dir }}-policy.d-03catalina.policy:
  file.managed:
    - name: {{ conf_dir }}/policy.d/03catalina.policy:
    - order: 100
    - source: salt://makina-states/files/{{ conf_dir }}/policy.d/03catalina.policy
    - template: jinja
    - defaults: {{ tomcat.defaultsData | yaml }}

{{ conf_dir }}-policy.d-01system.policy:
  file.managed:
    - name: {{ conf_dir }}/policy.d/01system.policy
    - order: 100
    - source: salt://makina-states/files/{{ conf_dir }}/policy.d/01system.policy
    - template: jinja
    - defaults: {{ tomcat.defaultsData | yaml }}

{{ conf_dir }}-policy.d-50local.policy:
  file.managed:
    - name: {{ conf_dir }}/policy.d/50local.policy
    - order: 100
    - source: salt://makina-states/files/{{ conf_dir }}/policy.d/50local.policy
    - template: jinja
    - defaults: {{ tomcat.defaultsData | yaml }}

{{ conf_dir }}-catalina.properties:
  file.managed:
    - name: {{ conf_dir }}/catalina.properties
    - order: 100
    - source: salt://makina-states/files/{{ conf_dir }}/catalina.properties
    - template: jinja
    - defaults: {{ tomcat.defaultsData | yaml }}

{{ conf_dir }}-server.xml:
  file.managed:
    - name: {{ conf_dir }}/server.xml
    - order: 100
    - source: salt://makina-states/files/{{ conf_dir }}/server.xml
    - template: jinja
    - defaults: {{ tomcat.defaultsData | yaml }}

{{ conf_dir }}-context.xml:
  file.managed:
    - name: {{ conf_dir }}/context.xml
    - order: 100
    - source: salt://makina-states/files/{{ conf_dir }}/context.xml
    - template: jinja
    - default: {{ tomcat.defaultsData | yaml }}

{{ conf_dir }}-server-xml-block1:
  file.blockreplace:
    - name: {{ conf_dir }}/server.xml
    - order: 200
    - marker_start: "<!-- salt managed zone: connector block -->"
    - marker_end: "<!-- end salt managed zone: connector block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True

{{ conf_dir }}-server-xml-block2:
  file.blockreplace:
    - name: {{ conf_dir }}/server.xml
    - order: 200
    - marker_start: "<!-- salt managed zone: serverend block -->"
    - marker_end: "<!-- end salt managed zone: serverend block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True

{{ conf_dir }}-server-xml-block3:
  file.blockreplace:
    - name: {{ conf_dir }}/server.xml
    - order: 200
    - marker_start: "<!-- salt managed zone: host block -->"
    - marker_end: "<!-- end salt managed zone: host block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True

{{ conf_dir }}-logging-properties-block1:
  file.blockreplace:
    - name: {{ conf_dir }}/logging.properties
    - order: 200
    - marker_start: '# salt managed zone: logging custom'
    - marker_end:  '# end salt managed zone: logging custom'
    - content: ''
    - backup: '.bak'
    - show_changes: True

{{ conf_dir }}-web-xml-block1:
  file.blockreplace:
    - name: {{ conf_dir }}/web.xml
    - order: 200
    - marker_start: "<!-- salt managed zone: begin block -->"
    - marker_end:  "<!-- salt managed zone: end block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True

{{ conf_dir }}-catalina-properties-block1:
  file.blockreplace:
    - name: {{ conf_dir }}/catalina.properties
    - order: 200
    - marker_start: '# salt managed zone: custom'
    - marker_end:  '# end salt managed zone: custom'
    - content: ''
    - backup: '.bak'
    - show_changes: True

{{ conf_dir }}-context-xml-block:
  file.blockreplace:
    - name: {{ conf_dir }}/context.xml
    - order: 200
    - marker_start: "<!-- salt managed zone: custom block -->"
    - marker_end: "<!-- end salt managed zone: custom block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True

{{ locs.conf_dir }}-default-tomcat{{ ver }}-block:
 file.blockreplace:
    - name: {{ locs.conf_dir }}/default/tomcat{{ ver }}
    - order: 200
    - marker_start: '# salt managed zone: custom'
    - marker_end:  '# end salt managed zone: custom'
    - content: ''
    - backup: '.bak'
    - show_changes: True

tomcat{{ ver }}:
  service.running:
    - order: last
    - watch:
      - pkg: tomcat-pkgs
      - file: {{ conf_dir }}-Catalina-localhost
      - file: {{ conf_dir }}-catalina-properties-block1
      - file: {{ conf_dir }}-catalina.properties
      - file: {{ conf_dir }}-context-xml-block
      - file: {{ conf_dir }}-context.xml
      - file: {{ conf_dir }}-logging-properties-block1
      - file: {{ conf_dir }}-logging.properties
      - file: {{ conf_dir }}-policy.d-01system.policy
      - file: {{ conf_dir }}-policy.d-02debian.policy
      - file: {{ conf_dir }}-policy.d-03catalina.policy
      - file: {{ conf_dir }}-policy.d-04webapps.policy
      - file: {{ conf_dir }}-policy.d-50local.policy
      - file: {{ conf_dir }}-server-xml-block1
      - file: {{ conf_dir }}-server-xml-block2
      - file: {{ conf_dir }}-server-xml-block3
      - file: {{ conf_dir }}-server.xml
      - file: {{ conf_dir }}-tomcat-users.xml
      - file: {{ conf_dir }}-web-xml-block1
      - file: {{ conf_dir }}-web.xml
      - file: {{ locs.conf_dir }}-default-tomcat{{ ver }}
      - file: {{ locs.conf_dir }}-default-tomcat{{ ver }}-block
