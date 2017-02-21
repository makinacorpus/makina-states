{% import "makina-states/services/http/apache/macros.sls" as macros with context %}
{% set apacheSettings = salt['mc_apache.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.http.apache.hooks

{#
# use now ondrej ppa with event by default & others mpm are bundled
apache-uninstall-others-mpms:
  pkg.removed:
    - pkgs:
      {{ macros.other_mpm_pkgs(apacheSettings.mpm) }}
    - require:
      - mc_proxy: makina-apache-post-pkgs
    - watch_in:
      - mc_proxy: makina-apache-post-inst
      - pkg: apache-mpm
apache-mpm:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: [apache2]
      {{ macros.mpm_pkgs(apacheSettings.mpm) }}
    - require:
      - mc_proxy: makina-apache-post-pkgs
    - watch_in:
      - mc_proxy: makina-apache-post-inst

#}

apache-repo:
  pkgrepo.managed:
    - humanname: apache ppa
    - name: deb http://ppa.launchpad.net/ondrej/apache2/ubuntu {{pkgssettings.udist}} main
    - dist: {{pkgssettings.udist}}
    - file: /etc/apt/sources.list.d/apacheppa.list
    - keyid: E5267A6C
    - keyserver: keyserver.ubuntu.com
    - require:
      - mc_proxy: makina-apache-post-pkgs
    - watch_in:
      - mc_proxy: makina-apache-post-inst
      - pkg: makina-apache-pkgs
#      - pkg: apache-mpm

# no more used in our ondrej ppa
#apache-mpm:
#  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
#    - pkgs: [apache2]
#    - require:
#      - mc_proxy: makina-apache-post-pkgs
#    - watch_in:
#      - mc_proxy: makina-apache-post-inst

makina-apache-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - watch:
      - mc_proxy: makina-apache-pre-inst
    - watch_in:
      - mc_proxy: makina-apache-post-inst
    - pkgs:
      {% for package in apacheSettings.packages %}
      - {{ package }}
      {% endfor %}
      - cronolog
