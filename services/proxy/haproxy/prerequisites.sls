{% import "makina-states/_macros/services.jinja" as services with context %}
{% set localsettings = services.localsettings %}
{% set haproxySettings = services.haproxySettings %}
{%- import "makina-states/_macros/localsettings.jinja" as localsettings with context %}
include:
  - makina-states.services.proxy.haproxy.hooks

{% if grains['os_family'] in ['Debian'] %}
{% set dist = localsettings.udist %}
{% endif %}
{% if grains['os'] in ['Debian'] %}
{% set dist = localsettings.ubuntu_lts %}
{% endif %}
base:
  pkgrepo.managed:
    - humanname: haproxy ppa
    - name: deb http://ppa.launchpad.net/vbernat/haproxy-1.5/ubuntu {{dist}} main

    - dist: precise
    - file: {{ localsettings.locations.conf_dir }}/apt/sources.list.d/haproxy.list
    - keyid: 1C61B9CD
    - keyserver: keyserver.ubuntu.com
    - require_in:
      - pkg: haproxy-pkgs

haproxy-pkgs:
  pkg.{{localsettings.installmode}}:
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
    - group: {{haproxySettings.group}}
    - watch:
      - mc_proxy: haproxy-pre-install-hook
    - watch_in:
      - mc_proxy: haproxy-post-install-hook

