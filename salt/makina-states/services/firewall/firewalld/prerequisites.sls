{% set data = salt['mc_firewalld.settings']() %}
{% set pkgssettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.firewall.firewalld.hooks
firewalld-repo:
  pkgrepo.managed:
    - humanname: firewalld ppa
    - name: deb http://ppa.launchpad.net/makinacorpus/firewalld/ubuntu {{pkgssettings.udist}} main
    - dist: {{pkgssettings.udist}}
    - file: /etc/apt/sources.list.d/firewalld.list
    - keyid: 207A7A4E
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: firewalld-preinstall
firewalld-pkgs:
  pkg.latest:
  #pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs: {{data.packages}}
    - require:
      - pkgrepo: firewalld-repo
    - require_in:
      - mc_proxy: firewalld-postinstall
