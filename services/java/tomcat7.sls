#
# Manage a tomcat7 installation via salt
# You can see in ./tomcat7-defaults.jinja the defaults associated with those states
# By default with use the java6 oracle jdk jvm
#
# You can override default settings in pillar via the 'tomcat7-default-settings:' key:
#
# For example:
#   tomcat7-default-settings:
#     java_home': /usr/lib/jvm/java-6-oracle
#
# Default settings:
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
#   port: default http port (8080)
#   ssl_port: default ssl port (8443)
#   ajp_port: default ajp port (8009)
#   defaultHost': default hostname (localhost)
#   welcome_files': list of files to serve as index (index.{htm,html,jsp})
#
# Custom configuration block, thx to file.accumulated, you can also add
# custom configuration blocks to some files:
#   - server.xml
#   - context.xml
#   - web.xml
#   - logging.properties
#   - catalina.properties
# See at the end of this state file for the appropriate blockreplace to use
# in your case
#
#

{% import "makina-states/services/java/tomcat7-defaults.jinja" as c with context %}
{% set conf_dir = c.defaultsData['conf_dir'] %}
{% set ver = c.defaultsData['ver'] %}

include:
  - makina-states.localsettings.jdk

tomcat-pkgs:
  pkg.installed:
    - names:
      - tomcat{{ver}}
    - require:
      - pkg: jdk-6-pkgs


/etc/default/tomcat{{ver}}:
  file.managed:
    - source: salt://makina-states/files/etc/default/tomcat{{ver}}
    - template: jinja
    - defaults: {{ c.defaultsData | yaml }}

{{conf_dir}}/web.xml:
  file.managed:
    - order: 100
    - source: salt://makina-states/files/{{conf_dir}}/web.xml
    - template: jinja
    - defaults: {{ c.defaultsData | yaml }}

{{conf_dir}}/Catalina/localhost:
  file.directory:
    - makedirs: true

{{conf_dir}}/tomcat-users.xml:
  file.managed:
    - order: 100
    - source: salt://makina-states/files/{{conf_dir}}/tomcat-users.xml
    - template: jinja
    - defaults: {{ c.defaultsData | yaml }}

{{conf_dir}}/logging.properties:
  file.managed:
    - source: salt://makina-states/files/{{conf_dir}}/logging.properties
    - order: 100
    - template: jinja
    - defaults: {{ c.defaultsData | yaml }}

{{conf_dir}}/policy.d/04webapps.policy:
  file.managed:
    - order: 100
    - source: salt://makina-states/files/{{conf_dir}}/policy.d/04webapps.policy
    - template: jinja
    - defaults: {{ c.defaultsData | yaml }}

{{conf_dir}}/policy.d/02debian.policy:
  file.managed:
    - order: 100
    - source: salt://makina-states/files/{{conf_dir}}/policy.d/02debian.policy
    - template: jinja
    - defaults: {{ c.defaultsData | yaml }}

{{conf_dir}}/policy.d/03catalina.policy:
  file.managed:
    - order: 100
    - source: salt://makina-states/files/{{conf_dir}}/policy.d/03catalina.policy
    - template: jinja
    - defaults: {{ c.defaultsData | yaml }}

{{conf_dir}}/policy.d/01system.policy:
  file.managed:
    - order: 100
    - source: salt://makina-states/files/{{conf_dir}}/policy.d/01system.policy
    - template: jinja
    - defaults: {{ c.defaultsData | yaml }}

{{conf_dir}}/policy.d/50local.policy:
  file.managed:
    - order: 100
    - source: salt://makina-states/files/{{conf_dir}}/policy.d/50local.policy
    - template: jinja
    - defaults: {{ c.defaultsData | yaml }}

{{conf_dir}}/catalina.properties:
  file.managed:
    - order: 100
    - source: salt://makina-states/files/{{conf_dir}}/catalina.properties
    - template: jinja
    - defaults: {{ c.defaultsData | yaml }}

{{conf_dir}}/server.xml:
  file.managed:
    - order: 100
    - source: salt://makina-states/files/{{conf_dir}}/server.xml
    - template: jinja
    - defaults: {{ c.defaultsData | yaml }}

{{conf_dir}}/context.xml:
  file.managed:
    - order: 100
    - source: salt://makina-states/files/{{conf_dir}}/context.xml
    - template: jinja
    - default: {{ c.defaultsData | yaml }}

{{conf_dir}}/server-xml-block1:
  file.blockreplace:
    - name: {{conf_dir}}/server.xml
    - order: 200
    - marker_start: "<!-- salt managed zone: connector block -->"
    - marker_end: "<!-- end salt managed zone: connector block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True

{{conf_dir}}/server-xml-block2:
  file.blockreplace:
    - name: {{conf_dir}}/server.xml
    - order: 200
    - marker_start: "<!-- salt managed zone: serverend block -->"
    - marker_end: "<!-- end salt managed zone: serverend block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True

{{conf_dir}}/server-xml-block3:
  file.blockreplace:
    - name: {{conf_dir}}/server.xml
    - order: 200
    - marker_start: "<!-- salt managed zone: host block -->"
    - marker_end: "<!-- end salt managed zone: host block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True

{{conf_dir}}/logging-properties-block1:
  file.blockreplace:
    - name: {{conf_dir}}/logging.properties
    - order: 200
    - marker_start: '# salt managed zone: logging custom'
    - marker_end:  '# end salt managed zone: logging custom'
    - content: ''
    - backup: '.bak'
    - show_changes: True

{{conf_dir}}/web.xml-block1:
  file.blockreplace:
    - name: {{conf_dir}}/web.xml
    - order: 200
    - marker_start: "<!-- salt managed zone: begin block -->"
    - marker_end:  "<!-- salt managed zone: end block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True

{{conf_dir}}/catalina-properties-block1:
  file.blockreplace:
    - name: {{conf_dir}}/catalina.properties
    - order: 200
    - marker_start: '# salt managed zone: custom'
    - marker_end:  '# end salt managed zone: custom'
    - content: ''
    - backup: '.bak'
    - show_changes: True

{{conf_dir}}/context-xml-block:
  file.blockreplace:
    - name: {{conf_dir}}/context.xml
    - order: 200
    - marker_start: "<!-- salt managed zone: custom block -->"
    - marker_end: "<!-- end salt managed zone: custom block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True

tomcat{{ver}}:
  service.running:
    - order: last
    - watch:
      - pkg: tomcat-pkgs
      - file: /etc/default/tomcat{{ver}}
      - file: {{conf_dir}}/web.xml
      - file: {{conf_dir}}/Catalina/localhost
      - file: {{conf_dir}}/tomcat-users.xml
      - file: {{conf_dir}}/logging.properties
      - file: {{conf_dir}}/policy.d/04webapps.policy
      - file: {{conf_dir}}/policy.d/02debian.policy
      - file: {{conf_dir}}/policy.d/03catalina.policy
      - file: {{conf_dir}}/policy.d/01system.policy
      - file: {{conf_dir}}/policy.d/50local.policy
      - file: {{conf_dir}}/catalina.properties
      - file: {{conf_dir}}/server.xml
      - file: {{conf_dir}}/context.xml
      - file: /etc/default/tomcat{{ver}}
      - file: {{conf_dir}}/server-xml-block2
      - file: {{conf_dir}}/server-xml-block3
      - file: {{conf_dir}}/context-xml-block

