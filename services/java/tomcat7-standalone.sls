{#-
# oracle jdk configuration
#   - makina-states/doc/ref/formulaes/services/java/tomcat7.rst
#}
{% import "makina-states/localsettings/jdk.sls" as jdk with context %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{% set localsettings = services.localsettings %}
{% set locs = salt['mc_localsettings.settings']()['locations'] %}
{% set data = services.tomcatSettings %}
{% set conf_dir = data.conf_dir %}
{% set ver = data.ver %}
{% set ydata = data|yaml %}
{% macro tomcat_watch() %}
      - mc_proxy: tomcat-post-install-hook
{% endmacro %}

{% macro tomcat_watch_in() %}
      - mc_proxy: tomcat-pre-restart-hook
{% endmacro %}
{% macro tomcat_block_watch_in() %}
      - mc_proxy: tomcat-pre-restart-hook
      - mc_proxy: tomcat-pre-blocks-hook
{% endmacro %}
{% macro do(full=False) %}
{{ salt['mc_macros.register']('services', 'java.tomcat7') }}
include:
{% if full %}
  - makina-states.localsettings.jdk
{% endif %}
  - makina-states.localsettings.jdk-hooks
  - makina-states.services.java.tomcat-hooks

{% if full %}
tomcat-{{ver}}-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - tomcat{{ ver }}
    - watch_in:
      - service: tomcat-{{ ver }}
    - require:
      - mc_proxy: makina-states-jdk_last
{% endif %}

{{ locs.conf_dir }}-default-tomcat{{ ver }}:
  file.managed:
    - name: {{ locs.conf_dir }}/default/tomcat{{ ver }}
    - source: salt://makina-states/files/etc/default/tomcat{{ ver }}
    - template: jinja
    - defaults: {{ ydata }}
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_block_watch_in() }}

{{ conf_dir }}-web.xml-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/web.xml
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/web.xml
    - template: jinja
    - defaults: {{ ydata }}
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_block_watch_in() }}

{{ conf_dir }}-Catalina-localhost-{{ver}}:
  file.directory:
    - name: {{ conf_dir }}/Catalina/localhost
    - makedirs: true
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_block_watch_in() }}

{{ conf_dir }}-tomcat-users.xml-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/tomcat-users.xml
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/tomcat-users.xml
    - template: jinja
    - defaults: {{ ydata }}
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_block_watch_in() }}

{{ conf_dir }}-logging.properties-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/logging.properties
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/logging.properties
    - template: jinja
    - defaults: {{ ydata }}
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_block_watch_in() }}

{{ conf_dir }}-policy.d-04webapps.policy-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/policy.d/04webapps.policy
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/policy.d/04webapps.policy
    - template: jinja
    - defaults: {{ ydata }}
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_block_watch_in() }}

{{ conf_dir }}-policy.d-02debian.policy-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/policy.d/02debian.policy
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/policy.d/02debian.policy
    - template: jinja
    - defaults: {{ ydata }}
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_block_watch_in() }}

{{ conf_dir }}-policy.d-03catalina.policy-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/policy.d/03catalina.policy
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/policy.d/03catalina.policy
    - template: jinja
    - defaults: {{ ydata }}
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_block_watch_in() }}

{{ conf_dir }}-policy.d-01system.policy-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/policy.d/01system.policy
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/policy.d/01system.policy
    - template: jinja
    - defaults: {{ ydata }}
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_block_watch_in() }}

{{ conf_dir }}-policy.d-50local.policy-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/policy.d/50local.policy
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/policy.d/50local.policy
    - template: jinja
    - defaults: {{ ydata }}
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_block_watch_in() }}

{{ conf_dir }}-catalina.properties-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/catalina.properties
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/catalina.properties
    - template: jinja
    - defaults: {{ ydata }}
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_block_watch_in() }}

{{ conf_dir }}-server.xml-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/server.xml
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/server.xml
    - template: jinja
    - defaults: {{ ydata }}
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_block_watch_in() }}

{{ conf_dir }}-context.xml-{{ver}}:
  file.managed:
    - name: {{ conf_dir }}/context.xml
    - source: salt://makina-states/files/etc/tomcat{{ ver }}/context.xml
    - template: jinja
    - default: {{ ydata }}
    - watch: {{ tomcat_watch() }}
    - watch_in: {{ tomcat_block_watch_in() }}

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

tomcat-{{ ver }}:
  service.running:
    - name: tomcat{{ ver }}
    - enable: true
    - watch_in:
      - mc_proxy: tomcat-pre-restart-hook
    - watch_in:
      - mc_proxy: tomcat-post-restart-hook
{% endmacro %}
{{do(full=False)}}
