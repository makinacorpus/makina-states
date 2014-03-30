{%- set localsettings = salt['mc_localsettings.settings']() %}
include:
  - makina-states.services.virt.lxc.hooks

lxc-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
{% if grains['os'] in ['Ubuntu'] -%}
{% if localsettings.udist in ['precise'] %}
    - fromrepo: {{localsettings.udist}}-backports
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
