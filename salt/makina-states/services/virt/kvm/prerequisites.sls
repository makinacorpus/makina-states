{%- set pkgSettings = salt['mc_pkgs.settings']() %}
include:
  - makina-states.services.virt.kvm.hooks
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
      {% if salt['mc_utils.loose_version'](grains.get('osrelease', '')) >= salt['mc_utils.loose_version']('20.04') %}
      - libvirt-clients
      {% else %}
      - libvirt-bin
      {% endif %}
      - libguestfs0
      - lvm2
      - libguestfs-tools
      - kpartx
      - ovmf
      - bridge-utils
      - libvirt-daemon
      - libvirt-daemon-system
    - watch_in:
      - mc_proxy: kvm-post-pkg
    - watch:
      - mc_proxy: kvm-pre-pkg
