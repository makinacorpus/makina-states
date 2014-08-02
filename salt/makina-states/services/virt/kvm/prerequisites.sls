{%- set pkgSettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.virt.kvm.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}

{% if grains['os'] in ['Ubuntu'] %}
{% set dist = pkgSettings.apt.ubuntu.dist %}
{% else %}
{% set dist = pkgSettings.apt.ubuntu.lts %}
{% endif %}
{% set locs = salt['mc_locations.settings']() %}

kvm-pkgs:
  {#pkg.{{salt['mc_pkgs.settings']()['installmode']}}: #}
  pkg.latest:
{# no need anymore -> ppa #}
{% if False and grains['os'] in ['Ubuntu'] -%}
{% if pkgSettings.udist in ['precise'] %}
    - fromrepo: {{pkgSettings.udist}}-backports
{% endif %}
{% endif %}
    - pkgs:
      - qemu-kvm
      - libvirt-bin
      - libguestfs0
      - lvm2
      - libguestfs-tools
      - kpartx
      - ovmf
      - bridge-utils
    - watch_in:
      - mc_proxy: kvm-post-pkg
    - watch:
      - mc_proxy: kvm-pre-pkg
{%endif %}
