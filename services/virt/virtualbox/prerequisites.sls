{% if salt['mc_controllers.mastersalt_mode']() %}
{%- set locs = salt['mc_locations.settings']() %}
include:
  - makina-states.services.virt.virtualbox.hooks
vb-base:
  pkgrepo.managed:
    - humanname: vbox ppa
    - name: deb http://download.virtualbox.org/virtualbox/debian trusty contrib
    - dist: trusty
    - file: /etc/apt/sources.list.d/vbox.list
    - key_url: https://www.virtualbox.org/download/oracle_vbox.asc
    - watch:
      - mc_proxy: ms-desktoptools-pkgm-pre
    - watch_in:
      - mc_proxy: ms-desktoptools-pkgm-post

virtualbox-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - watch:
      - pkgrepo: vb-base
      - mc_proxy: virtualbox-pre-install
    - watch_in:
      - mc_proxy: virtualbox-post-install
    - pkgs:
      - virtualbox-4.3
      - dkms
{% endif %}
