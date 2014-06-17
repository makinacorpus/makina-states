{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set haproxySettings = salt['mc_haproxy.settings']() %}
include:
  - makina-states.services.proxy.haproxy.hooks

{% if grains['os_family'] in ['Debian'] %}
{% set dist = pkgssettings.udist %}
{% endif %}
{% if grains['os'] in ['Debian'] %}
{% set dist = pkgssettings.ubuntu_lts %}
{% endif %}
haproxy-base:
  pkgrepo.managed:
    - humanname: haproxy ppa
    - name: deb http://ppa.launchpad.net/vbernat/haproxy-1.5/ubuntu {{dist}} main

    - dist: {{dist}}
    - file: {{ salt['mc_locations.settings']().conf_dir }}/apt/sources.list.d/haproxy.list
    - keyid: 1C61B9CD
    - keyserver: keyserver.ubuntu.com
    - require_in:
      - pkg: haproxy-pkgs

haproxy-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - haproxy
    - watch:
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

