{%- set pkgSettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.virt.lxc.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}

{% if grains['os'] in ['Ubuntu'] %}
{% set dist = pkgSettings.apt.ubuntu.dist %}
{% else %}
{% set dist = pkgSettings.apt.ubuntu.lts %}
{% endif %}
{% set locs = salt['mc_locations.settings']() %}
lxc-repo:
  pkgrepo.managed:
    - name: lxc
    - humanname: LXC PPA
    - name: deb http://ppa.launchpad.net/ubuntu-lxc/stable/ubuntu {{dist}} main
    - dist: {{dist}}
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
{% if pkgSettings.udist in ['precise'] %}
    - fromrepo: {{pkgSettings.udist}}-backports
{% endif %}
{% endif %}
    - pkgs:
      - lxc
      - lxctl
      - dnsmasq
    - watch_in:
      - mc_proxy: lxc-post-pkg
    - watch:
      - mc_proxy: lxc-pre-pkg
      - pkgrepo: lxc-repo
{%endif %}
