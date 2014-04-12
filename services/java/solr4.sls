# {#
# Solr 4 configuration
# - We create a basic multicore solr install
# Layout followx the following scheme
#
# {{ locs.srv_dir }}/solr/4
#     download
#     home
#        core_name
#
# - It is up to each solr consumer
#   - to create its own core configuration files in {{ locs.srv_dir }}/solr/4/home/<core>
#   - to register this core in the main configuration:
#    - via the register_core macro (see the register_core macro below)::
#       eg:  {{register_macro(NAME, CONF_DIR, DATADIR=conf_dir/data }}
#
#    - via the cores default data (see defaults)
#
# The webapp is mounted on tomcat under the /solr4/ path
# #}
{% import "makina-states/services/java/tomcat7-defaults.jinja" as tomcat with context %}
{% import "makina-states/services/java/solr4-defaults.jinja" as solr with context %}
{{ salt['mc_macros.register']('services', 'java.solr4') }}
{% set locs = salt['mc_locations.settings']() %}
{% set ugs = salt['mc_usergroup.settings']() %}

include:
  - makina-states.localsettings.jdk
  - makina-states.services.java.tomcat7

{% set tconf_dir = tomcat.defaultsData['conf_dir'] %}
{% set tdata = tomcat.defaultsData %}
{% set data = solr.defaultsData %}
{% set tver = tomcat.defaultsData['ver'] %}
{% set v =  data['ver'] %}
{% set fv = data['full_ver'] %}
{% set groot =  data['global_root_dir'] %}
{% set root =  data['root_dir'] %}
{% set webapp_dir =  data['webapp_dir'] %}
{% set home_dir =  data['home_dir'] %}
{% set data_dir =  data['data_dir'] %}
{% set conf_dir =  data['conf_dir'] %}
{% set dl_dir =  data['dl_dir'] %}

{% macro register_core(core_name, conf_dir, cdata_dir=None, stateid=None)  %}
{% if not stateid %} {% set stateid = core_name %} {% endif %}
{% if not cdata_dir %} {% set cdata_dir = data_dir + '/' + core_name %} {% endif %}
{{ stateid }}-datadir-{{ v }}:
  file.directory:
    - name: {{ cdata_dir }}
    - makedirs: True

{{ stateid }}-block-solr-{{ v }}:
  file.accumulated:
    - filename: {{ home_dir }}/solr.xml
    - text: |
            <core name="{{ core_name }}" instanceDir="{{ conf_dir }}">
              <property name="dataDir" value="{{ cdata_dir }}" />
            </core>
    - watch_in:
      - service: tomcat7
    - require:
      - file: {{ stateid }}-datadir-{{ v }}
    - require_in:
      - cmd: {{ groot }}-reset-perms
      - file: fill-block-solrxml-{{ v }}
{% endmacro %}

{% set ydata = salt['mc_utils.json_dump'](data) %}
solr{{ v }}-prerequisites:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - rsync
      - unzip

{{ root }}-solr-{{ v }}:
  file.directory:
    - name: {{ root }}
    - makedirs: true
    - order: 1
    - require:
      - pkg: solr{{ v }}-prerequisites

{{ dl_dir }}-solr-{{ v }}:
  file.directory:
    - name: {{ dl_dir }}
    - makedirs: true
  cmd.run:
    - name: >
            wget -c http://apache.mirrors.multidist.eu/lucene/solr/{{ fv }}/solr-{{ fv }}.tgz &&
            tar xzf solr-{{ fv }}.tgz &&
            touch {{ dl_dir }}/solr-{{ fv }}/.download
    - cwd: {{ dl_dir }}
    - unless: |
              test -e {{ locs.srv_dir }}/solr/{{ v }}/download/solr-{{ fv }}/.download


{{ webapp_dir }}-solr-{{ v }}:
  file.directory:
    - name: {{ webapp_dir }}
    - makedirs: true
    - require:
      - cmd: {{ dl_dir }}-solr-{{ v }}
  cmd.run:
    - require:
      - file: {{ home_dir }}-solr-{{ v }}
    - name: >
            unzip -qq -o dist/*solr*war -d {{ webapp_dir }}/solr &&
            cp dist/*jar dist/*/*jar   {{ webapp_dir }}/solr/WEB-INF/lib
    - cwd: {{ dl_dir }}/solr-{{ fv }}
    - unless: |
              test -d "{{ webapp_dir }}/solr" && test -e "{{ webapp_dir }}/solr/WEB-INF/lib/slf4j-api-"*.jar

{{ data_dir }}-solr-{{ v }}:
  file.directory:
    - name: {{ data_dir }}
    - makedirs: true
    - require:
      - cmd: {{ dl_dir }}-solr-{{ v }}
    - require_in:
      - service: tomcat7

{{ home_dir }}-solr-{{ v }}:
  file.directory:
    - name: {{ home_dir }}
    - makedirs: true
    - require:
      - cmd: {{ dl_dir }}-solr-{{ v }}


zoocfg-{{ v }}:
  file.managed:
    - order: 100
    - source: salt://makina-states/files{{ home_dir }}/zoo.cfg
    - cfg: |
           {{ydata}}
    - name: {{ home_dir }}/zoo.cfg
    - mode: 0770
    - template: jinja
    - user: {{ tdata['tomcat_user'] }}
    - group: {{ ugs.group }}
    - watch_in:
      - service: tomcat7
    - require:
        - file: {{ home_dir }}-solr-{{ v }}

solrxml-{{ v }}:
  file.managed:
    - source: salt://makina-states/files{{ home_dir }}/solr.xml
    - name: {{ home_dir }}/solr.xml
    - order: 100
    - mode: 0770
    - cfg: |
           {{ydata}}
    - user: {{ tdata['tomcat_user'] }}
    - group: {{ ugs.group }}
    - template: jinja
    - watch_in:
      - service: tomcat7
    - require:
        - file: {{ home_dir }}-solr-{{ v }}

solr-default-core-{{ v }}:
  file.recurse:
    - order: 100
    - source: salt://makina-states/files{{ home_dir }}/default
    - name: {{ home_dir }}/default
    - user: {{ tdata['tomcat_user'] }}
    - group: {{ ugs.group }}
    - require:
      - file: {{ home_dir }}-solr-{{ v }}

{% for i in  ['dist', 'contrib']: %}
l-{{ i }}-solr-{{ v }}:
  file.symlink:
    - name: {{ root }}/{{ i }}
    - target: {{ dl_dir }}/solr-{{ fv }}/{{ i }}
    - makedirs: True
    - force: True
    - watch_in:
      - service: tomcat7
    - require:
      - file: {{ root }}
{% endfor %}

fill-block-solrxml-{{ v }}:
  file.blockreplace:
    - name: {{ home_dir }}/solr.xml
    - order: 200
    - marker_start: "<!-- salt managed zone: custom block -->"
    - marker_end: "<!-- end salt managed zone: custom block -->"
    - content: ''
    - backup: '.bak'
    - show_changes: True
    - require_in:
      - service: tomcat7

{{ tconf_dir }}-Catalina-localhost-solr4.xml:
  file.managed:
    - name: {{ tconf_dir }}/Catalina/localhost/solr4.xml
    - source: salt://makina-states/files/{{ tconf_dir }}/Catalina/localhost/solr4.xml
    - watch_in:
      - service: tomcat7
    - order: 100
    - mode: 0770
    - cfg: |
           {{ydata}}
    - user: {{ tdata['tomcat_user'] }}
    - group: {{ ugs.group }}
    - template: jinja

{# handled directly in solr.xml template
{% for core in data['cores'] %}
{{register_core(core['name'], core['dir'])}}
{% endfor%}
#}

# fix perms
{{ groot }}-reset-perms:
  cmd.run:
    - name: >
            {{ locs.resetperms }}
            --paths "{{ solr.groot }}"
            --dmode '0770' --fmode 0770
            -u {{ tdata['tomcat_user'] }} -g {{ ugs.group }}
    - require:
      - file: fill-block-solrxml-{{ v }}
      - file: solr-default-core-{{ v }}
      - cmd: {{ webapp_dir }}-solr-{{ v }}
      - file: {{ tconf_dir }}-Catalina-localhost-solr4.xml
      - file: {{ data_dir }}-solr-{{ v }}
      - cmd: {{ dl_dir }}-solr-{{ v }}
    - require_in:
      - service: tomcat7

# vim:set nofoldenable #
