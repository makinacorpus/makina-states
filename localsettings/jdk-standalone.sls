{#-
# oracle jdk configuration
#   - makina-states/doc/ref/formulaes/localsettings/jdk.rst
#}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{%- set locs = localsettings.locations %}

{% macro jdk_pkgs(ver, suf='') %}
jdk-{{ ver }}-pkgs{{suf}}:
  cmd.run:
    - name: sudo echo oracle-java{{ ver }}-installer shared/accepted-oracle-license-v1-1 select true | sudo {{ locs.bin_dir }}/debconf-set-selections;
    - unless: test "$({{ locs.bin_dir }}/debconf-get-selections |grep shared/accepted-oracle-license-v1-1|grep oracle-java{{ ver }}-installer|grep true|wc -l)" != 0;
  pkg.installed:
    - names:
      - oracle-java{{ ver }}-installer
    - require:
      - pkgrepo: jdk-repo
      - cmd: jdk-{{ ver }}-pkgs
{% endmacro %}
{% macro do(full=False) %}
{{ salt['mc_macros.register']('localsettings', 'jdk') }}
{% if grains['os_family'] in ['Debian'] %}
{% set dist = localsettings.udist %}
{% endif %}
{% if grains['os'] in ['Debian'] %}
{% set dist = localsettings.ubuntu_lts %}
{% endif %}
{%- set default_ver = localsettings.jdkDefaultVer %}
include:
  - makina-states.localsettings.jdk-hooks
{% if full %}
jdk-repo:
  pkgrepo.managed:
    - watch:
      - mc_proxy: makina-states-jdk_begin
    - name: deb http://ppa.launchpad.net/webupd8team/java/ubuntu {{ dist }} main
    - file: {{ locs.conf_dir }}/apt/sources.list.d/webupd8team.list
    - keyid: EEA14886
    - keyserver: keyserver.ubuntu.com

{% for ver in '6', '7' %}
{{ jdk_pkgs(ver) }}
{% endfor %}
java-{{ default_ver }}-install:
  pkg.installed:
    - pkgs: [oracle-java{{ default_ver }}-set-default]
    - require:
      - pkg: jdk-{{ default_ver }}-pkgs
    - watch_in:
      - mc_proxy: makina-states-jdk_last
{% endif %}
{% endmacro %}
{{ do(full=False)}}
