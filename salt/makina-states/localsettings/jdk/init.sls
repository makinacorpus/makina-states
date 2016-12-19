{#-
# oracle jdk configuration
#   - makina-states/doc/ref/formulaes/localsettings/jdk.rst
#}
{%- set javas = salt['mc_java.settings']() %}
{%- set locs = salt['mc_locations.settings']() %}

{% macro jdk_pkgs(ver, suf='') %}
jdk-{{ ver }}-pkgs{{suf}}:
  cmd.run:
    - name: sudo echo oracle-java{{ ver }}-installer shared/accepted-oracle-license-v1-1 select true | sudo {{ locs.bin_dir }}/debconf-set-selections;
    - unless: test "$({{ locs.bin_dir }}/debconf-get-selections |grep shared/accepted-oracle-license-v1-1|grep oracle-java{{ ver }}-installer|grep true|wc -l)" != 0;
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - names:
      - oracle-java{{ ver }}-installer
    - require:
      - pkgrepo: jdk-repo
      - cmd: jdk-{{ ver }}-pkgs
    - watch_in:
      - mc_proxy: makina-states-jdk_last
{% endmacro %}
{{ salt['mc_macros.register']('localsettings', 'jdk') }}
{%- set default_ver = javas.default_jdk_ver %}

include:
  - makina-states.localsettings.jdk.hooks

jdk-repo:
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
    - watch:
      - mc_proxy: makina-states-jdk_begin
    - name: deb http://ppa.launchpad.net/webupd8team/java/ubuntu {{ salt['mc_pkgs.settings']().udist }} main
    - file: {{ locs.conf_dir }}/apt/sources.list.d/webupd8team.list
    - keyid: EEA14886
    - keyserver: keyserver.ubuntu.com

{% for ver in javas.installed %}
{{ jdk_pkgs(ver) }}
{% endfor %}

java-{{ default_ver }}-install:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: [oracle-java{{ default_ver }}-set-default]
    - require:
      - pkg: jdk-{{ default_ver }}-pkgs
    - watch_in:
      - mc_proxy: makina-states-jdk_last