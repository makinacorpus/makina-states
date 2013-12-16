#
# Install oracle & other JDKs on a system
#

{% set dist = salt['grains.get']('lsb_distrib_codename', 'precise') %}
{% set default_ver = '7' %}

jdk-repo:
  pkgrepo.managed:
    - name: deb http://ppa.launchpad.net/webupd8team/java/ubuntu {{dist}} main
    - file: /etc/apt/sources.list.d/webupd8team.list
    - keyid: EEA14886
    - keyserver: keyserver.ubuntu.com

{% for ver in '6', '7' %}
jdk-{{ver}}-pkgs:
  cmd.run:
    - name: sudo echo oracle-java{{ver}}-installer shared/accepted-oracle-license-v1-1 select true | sudo /usr/bin/debconf-set-selections;
    - unless: test "$(/usr/bin/debconf-get-selections |grep shared/accepted-oracle-license-v1-1|grep oracle-java{{ver}}-installer|grep true|wc -l)" != 0;
  pkg.installed:
    - names:
      - oracle-java{{ver}}-installer
    - require:
      - pkgrepo: jdk-repo
      - cmd: jdk-{{ver}}-pkgs
{% endfor %}

java-{{default_ver}}-install:
  pkg.installed:
    - pkgs: [oracle-java{{default_ver}}-set-default]
    - require:
      - pkg: jdk-{{default_ver}}-pkgs
