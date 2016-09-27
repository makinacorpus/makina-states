{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set haproxySettings = salt['mc_haproxy.settings']() %}
include:
  - makina-states.services.proxy.haproxy.hooks
  - makina-states.localsettings.insserv

{% set f = salt['mc_locations.settings']().conf_dir + '/apt/sources.list.d/haproxy.list' %}

haproxy-base:
  cmd.run:
    - name: sed -i "/makinacorpus/ d" "{{f}}" && echo changed='false'
    - onlyif: test -e "{{f}}"
    #- name: sed -i "/vbernat/ d" "{{f}}" && echo changed='false'
    - stateful: true
    - watch:
      - mc_proxy: haproxy-pre-install-hook
    - watch_in:
      - mc_proxy: haproxy-pre-hardrestart-hook
      - mc_proxy: haproxy-post-install-hook
  pkgrepo.managed:
    - humanname: haproxy ppa
    - name: deb http://ppa.launchpad.net/vbernat/haproxy-1.5/ubuntu {{pkgssettings.udist}} main
    - dist: {{pkgssettings.udist}}
    - file: "{{f}}"
    - keyid: 207A7A4E
    - keyserver: keyserver.ubuntu.com
    - require:
      - cmd: haproxy-base
    - require_in:
      - pkg: haproxy-pkgs

haproxy-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - haproxy
    - watch:
      - mc_proxy: localsettings-inssserv-post
      - mc_proxy: haproxy-pre-install-hook
    - watch_in:
      - mc_proxy: haproxy-pre-hardrestart-hook
      - mc_proxy: haproxy-post-install-hook

group-haproxy:
  group.present:
    - name: {{haproxySettings.group}}
user-haproxy:
  user.present:
    - name: {{haproxySettings.user}}
    - system: true
    - optional_groups: {{haproxySettings.group}}
    - remove_groups: false
    - watch:
      - mc_proxy: haproxy-pre-install-hook
    - watch_in:
      - mc_proxy: haproxy-post-install-hook
