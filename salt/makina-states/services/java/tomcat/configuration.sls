include:
  - makina-states.services.java.tomcat.hooks
  - makina-states.services.java.tomcat.services

{% set data = salt['mc_tomcat.settings']() %}
{% set ver = data.ver %}
{% set locs = salt['mc_locations.settings']() %}
{% set conf_dir = data.conf_dir %}
{% set ydata = salt['mc_utils.json_dump'](data) %}
{% macro tomcatc_watch() %}
      - mc_proxy: tomcat-pre-conf-hook
{% endmacro %}
{% macro tomcatc_watch_in() %}
      - mc_proxy: tomcat-post-conf-hook
{% endmacro %}



{% macro tomcat_watch() %}
      - mc_proxy: tomcat-pre-blocks-hook
{% endmacro %}
{% macro tomcat_watch_in() %}
      - mc_proxy: tomcat-post-blocks-hook
{% endmacro %}


{{ locs.conf_dir }}-default-tomcat{{ ver }}:
  file.managed:
    - name: {{ locs.conf_dir }}/default/tomcat{{ ver }}
    - source: salt://makina-states/files/etc/default/tomcat{{ ver }}
    - template: jinja
    - defaults:
      data: |
            {{ ydata }}
    - watch: {{ tomcatc_watch() }}
    - watch_in: {{ tomcatc_watch_in() }}

{{ conf_dir }}-web.xml-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/web.xml
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/web.xml
    - template: jinja
    - defaults:
      data: |
            {{ ydata }}
    - watch: {{ tomcatc_watch() }}
    - watch_in: {{ tomcatc_watch_in() }}

{{ conf_dir }}-Catalina-localhost-{{ver}}:
  file.directory:
    - name: {{ conf_dir }}/Catalina/localhost
    - makedirs: true
    - watch: {{ tomcatc_watch() }}
    - watch_in: {{ tomcatc_watch_in() }}

{{ conf_dir }}-tomcat-users.xml-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/tomcat-users.xml
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/tomcat-users.xml
    - template: jinja
    - defaults:
      data: |
            {{ ydata }}
    - watch: {{ tomcatc_watch() }}
    - watch_in: {{ tomcatc_watch_in() }}

{{ conf_dir }}-logging.properties-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/logging.properties
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/logging.properties
    - template: jinja
    - defaults:
      data: |
            {{ ydata }}
    - watch: {{ tomcatc_watch() }}
    - watch_in: {{ tomcatc_watch_in() }}

{{ conf_dir }}-policy.d-04webapps.policy-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/policy.d/04webapps.policy
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/policy.d/04webapps.policy
    - template: jinja
    - defaults:
      data: |
            {{ ydata }}
    - watch: {{ tomcatc_watch() }}
    - watch_in: {{ tomcatc_watch_in() }}

{{ conf_dir }}-policy.d-02debian.policy-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/policy.d/02debian.policy
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/policy.d/02debian.policy
    - template: jinja
    - defaults:
      data: |
            {{ ydata }}
    - watch: {{ tomcatc_watch() }}
    - watch_in: {{ tomcatc_watch_in() }}

{{ conf_dir }}-policy.d-03catalina.policy-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/policy.d/03catalina.policy
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/policy.d/03catalina.policy
    - template: jinja
    - defaults:
      data: |
            {{ ydata }}
    - watch: {{ tomcatc_watch() }}
    - watch_in: {{ tomcatc_watch_in() }}

{{ conf_dir }}-policy.d-01system.policy-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/policy.d/01system.policy
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/policy.d/01system.policy
    - template: jinja
    - defaults:
      data: |
            {{ ydata }}
    - watch: {{ tomcatc_watch() }}
    - watch_in: {{ tomcatc_watch_in() }}

{{ conf_dir }}-policy.d-50local.policy-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/policy.d/50local.policy
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/policy.d/50local.policy
    - template: jinja
    - defaults:
      data: |
            {{ ydata }}
    - watch: {{ tomcatc_watch() }}
    - watch_in: {{ tomcatc_watch_in() }}

{{ conf_dir }}-catalina.properties-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/catalina.properties
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/catalina.properties
    - template: jinja
    - defaults:
      data: |
            {{ ydata }}
    - watch: {{ tomcatc_watch() }}
    - watch_in: {{ tomcatc_watch_in() }}

{{ conf_dir }}-server.xml-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/server.xml
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/server.xml
    - template: jinja
    - defaults:
      data: |
            {{ ydata }}
    - watch: {{ tomcatc_watch() }}
    - watch_in: {{ tomcatc_watch_in() }}

{{ conf_dir }}-context.xml-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/context.xml
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/context.xml
    - template: jinja
    - default:
      data: |
            {{ ydata }}
    - watch: {{ tomcatc_watch() }}
    - watch_in: {{ tomcatc_watch_in() }}

{{ conf_dir }}-server-xml-block1-{{ver}}:
  file.blockreplace:
    - name: {{ conf_dir }}/server.xml
    - marker_start: "<!-- salt managed zone: connector block -->"
    - marker_end: "<!-- end salt managed zone: connector block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_watch_in() }}

{{ conf_dir }}-server-xml-block2-{{ver}}:
  file.blockreplace:
    - name: {{ conf_dir }}/server.xml
    - marker_start: "<!-- salt managed zone: serverend block -->"
    - marker_end: "<!-- end salt managed zone: serverend block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_watch_in() }}

{{ conf_dir }}-server-xml-block3-{{ver}}:
  file.blockreplace:
    - name: {{ conf_dir }}/server.xml
    - marker_start: "<!-- salt managed zone: host block -->"
    - marker_end: "<!-- end salt managed zone: host block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_watch_in() }}

{{ conf_dir }}-logging-properties-block1-{{ver}}:
  file.blockreplace:
    - name: {{ conf_dir }}/logging.properties
    - marker_start: '# salt managed zone: logging custom'
    - marker_end:  '# end salt managed zone: logging custom'
    - content: ''
    - backup: '.bak'
    - show_changes: True
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_watch_in() }}

{{ conf_dir }}-web-xml-block1-{{ver}}:
  file.blockreplace:
    - name: {{ conf_dir }}/web.xml
    - marker_start: "<!-- salt managed zone: begin block -->"
    - marker_end:  "<!-- salt managed zone: end block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_watch_in() }}

{{ conf_dir }}-catalina-properties-block1-{{ver}}:
  file.blockreplace:
    - name: {{ conf_dir }}/catalina.properties
    - marker_start: '# salt managed zone: custom'
    - marker_end:  '# end salt managed zone: custom'
    - content: ''
    - backup: '.bak'
    - show_changes: True
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_watch_in() }}

{{ conf_dir }}-context-xml-block-{{ver}}:
  file.blockreplace:
    - name: {{ conf_dir }}/context.xml
    - marker_start: "<!-- salt managed zone: custom block -->"
    - marker_end: "<!-- end salt managed zone: custom block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_watch_in() }}

{{ locs.conf_dir }}-default-tomcat{{ ver }}-block-{{ver}}:
 file.blockreplace:
    - name: {{ locs.conf_dir }}/default/tomcat{{ ver }}
    - marker_start: '# salt managed zone: custom'
    - marker_end:  '# end salt managed zone: custom'
    - content: ''
    - backup: '.bak'
    - show_changes: True
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_watch_in() }}

