{%- set pkgssettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.virt.lxc.hooks
{% set locs = salt['mc_locations.settings']() %}
{%- set vmdata = salt['mc_cloud_vm.settings']() %}
{%- set data = vmdata.vts.lxc %}
{% if grains['os'] in ['Ubuntu'] and grains['osrelease'] >= '16.04' %}
lxc-repo:
  file.absent:
    - names:
      - {{locs.conf_dir}}/apt/sources.list.d/lxcmc.list
      - {{locs.conf_dir}}/apt/sources.list.d/lxc.list
    - watch_in:
      - cmd: lxc-repo
      - pkg: lxc-pkgs
  cmd.watch:
    - name: apt-get update && echo changed=false
    - stateful: true
    - watch_in:
      - pkg: lxc-pkgs

{% else %}
lxc-repo:
  {# 04/06/2015: lxcfs & lxc are utterly bugged in stable #}
  cmd.run:
    #- name: sed -i -re "/stable/d" {{locs.conf_dir}}/apt/sources.list.d/lxc.list && echo changed='false'
    - name: sed -i -re "/daily/d" {{locs.conf_dir}}/apt/sources.list.d/lxc.list && echo changed='false'
    - stateful: true
    - onlyif: test -e {{locs.conf_dir}}/apt/sources.list.d/lxc.list
    - watch:
      - mc_proxy: lxc-pre-pkg
    - watch_in:
      - pkgrepo: lxc-repo
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
    #- name: deb http://ppa.launchpad.net/ubuntu-lxc/daily/ubuntu {{pkgssettings.udist}} main
    - name: deb http://ppa.launchpad.net/ubuntu-lxc/stable/ubuntu {{pkgssettings.udist}} main
    - file: {{locs.conf_dir}}/apt/sources.list.d/lxc.list
    - keyid: 7635B973
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: lxc-pre-pkg
    - watch_in:
      - pkg: lxc-pkgs
{% endif %}

mclxc-repo:
  file.absent:
    - name: {{locs.conf_dir}}/apt/sources.list.d/lxcmc.list
    - watch_in:
      - pkg: lxc-pkgs
  {# 04/06/2015: lxcfs & lxc are utterly bugged in stable #}
  {#
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
    - name: lxc
    - humanname: LXCMC PPA
    - name: deb http://ppa.launchpad.net/makinacorpus/lxc/ubuntu {{pkgssettings.udist}} main
    - dist: {{pkgssettings.udist}}
    - file: {{locs.conf_dir}}/apt/sources.list.d/lxcmc.list
    - keyid: 207A7A4E
    - keyserver: keyserver.ubuntu.com
    - watch:
      - mc_proxy: lxc-pre-pkg
  #}

lxc-pkgs:
  {#pkg.{{salt['mc_pkgs.settings']()['installmode']}}: #}
  pkg.latest:
{# no need anymore -> ppa #}
{% if False and grains['os'] in ['Ubuntu'] -%}
{% if pkgssettings.udist in ['precise'] %}
    - fromrepo: {{pkgssettings.udist}}-backports
{% endif %}
{% endif %}
    - pkgs: [{{', '.join(data.pkgs)}}]
    - watch_in:
      - mc_proxy: lxc-post-pkg
    - watch:
      - mc_proxy: lxc-pre-pkg