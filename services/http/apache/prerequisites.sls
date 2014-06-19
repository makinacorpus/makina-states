{% import "makina-states/services/http/apache/macros.sls" as macros with context %}
{% set apacheSettings = salt['mc_apache.settings']() %}
include:
  - makina-states.services.http.apache.hooks

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
    - pkgs:
      {{ macros.mpm_pkgs(apacheSettings.mpm) }}
    - require:
      - mc_proxy: makina-apache-post-pkgs
    - watch_in:
      - mc_proxy: makina-apache-post-inst

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

