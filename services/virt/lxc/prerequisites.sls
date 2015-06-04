{%- set pkgssettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.virt.lxc.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}

{% set locs = salt['mc_locations.settings']() %}
lxc-repo:
  {# 04/06/2015: lxcfs & lxc are utterly bugged in stable #}
  cmd.run:
    - name: sed -i -re "/stable/d" {{locs.conf_dir}}/apt/sources.list.d/lxc.list && echo changed='false'
    - stateful: true
    - onlyif: test -e {{locs.conf_dir}}/apt/sources.list.d/lxc.list
    - watch:
      - mc_proxy: lxc-pre-pkg
    - watch_in:
      - pkgrepo: lxc-repo
  pkgrepo.managed:
    - name: lxc
    - humanname: LXC PPA
    #- name: deb http://ppa.launchpad.net/ubuntu-lxc/stable/ubuntu {{pkgssettings.ppa_dist}} main
    - name: deb http://ppa.launchpad.net/ubuntu-lxc/daily/ubuntu {{pkgssettings.ppa_dist}} main
    - dist: {{pkgssettings.ppa_dist}}
    - file: {{locs.conf_dir}}/apt/sources.list.d/lxc.list
    - keyid: 7635B973
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: lxc-pre-pkg

lxc-pkgs:
  {#pkg.{{salt['mc_pkgs.settings']()['installmode']}}: #}
  pkg.latest:
{# no need anymore -> ppa #}
{% if False and grains['os'] in ['Ubuntu'] -%}
{% if pkgssettings.udist in ['precise'] %}
    - fromrepo: {{pkgssettings.udist}}-backports
{% endif %}
{% endif %}
    - pkgs:
      - lxc-templates
      - lxc
      - lxctl
      - python3-lxc
      - liblxc1
      - lxcfs
      - cgmanager
      - dnsmasq
    - watch_in:
      - mc_proxy: lxc-post-pkg
    - watch:
      - mc_proxy: lxc-pre-pkg
      - pkgrepo: lxc-repo
{%endif %}
