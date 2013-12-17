#
# Install oracle & other JDKs on a system
#
{% import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
{% set locs = localsettings.locations %}
{% if grains['os_family'] in ['Debian'] %}
{% if grains['os'] != 'Ubuntu' %}
FAILHARD
  - PORT ME
{% else %}
{{ localsettings.register('jdk') }}
{% endif %}

{% set dist = localsettings.udist %}
{% set default_ver = localsettings.jdkDefaultVer %}
jdk-repo:
  pkgrepo.managed:
    - name: deb http://ppa.launchpad.net/webupd8team/java/ubuntu {{ dist }} main
    - file: {{ locs.conf_dir }}/apt/sources.list.d/webupd8team.list
    - keyid: EEA14886
    - keyserver: keyserver.ubuntu.com

{% for ver in '6', '7' %}
jdk-{{ ver }}-pkgs:
  cmd.run:
    - name: sudo echo oracle-java{{ ver }}-installer shared/accepted-oracle-license-v1-1 select true | sudo {{ locs.bin_dir }}/debconf-set-selections;
    - unless: test "$({{ locs.bin_dir }}/debconf-get-selections |grep shared/accepted-oracle-license-v1-1|grep oracle-java{{ ver }}-installer|grep true|wc -l)" != 0;
  pkg.installed:
    - names:
      - oracle-java{{ ver }}-installer
    - require:
      - pkgrepo: jdk-repo
      - cmd: jdk-{{ ver }}-pkgs
{% endfor %}

java-{{ default_ver }}-install:
  pkg.installed:
    - pkgs: [oracle-java{{ default_ver }}-set-default]
    - require:
      - pkg: jdk-{{ default_ver }}-pkgs

{% endif %}
