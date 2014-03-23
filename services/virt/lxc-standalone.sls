{#-
# define in pillar an entry "*-lxc-container-def
# as:
# toto-lxc-container-def:
#  name: theservername (opt, take "toto" as servername otherwise)
#  mac: 00:16:3e:04:60:bd
#  ip4: 10.0.3.2
#  netmask: 255.255.255.0 (opt)
#  gateway: 10.0.3.1 (opt)
#  dnsservers: 10.0.3.1 (opt)
#  template: ubuntu (opt)
#  rootfs: root directory (opt)
#  config: config path (opt)
# and it will create an ubuntu templated lxc host
#}
{{ salt['mc_macros.register']('services', 'virt.lxc') }}
{%- set localsettings = salt['mc_localsettings.settings']() %}
{%- set locs = localsettings['locations'] %}
{% macro do(full=True) %}
include:
  - makina-states.services.virt.lxc-hooks

{% if full %}
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
{% endif %}
{% if grains['os'] in ['Debian'] -%}
lxc-ubuntu-template:
  file.managed:
    - name: /usr/share/lxc/templates/lxc-ubuntu
    - source: salt://makina-states/files/usr/share/lxc/templates/lxc-ubuntu
    - mode: 750
    - user: root
    - group: root
    - require_in:
      - service: lxc-services-enabling
      - file: lxc-after-maybe-bind-root

lxc-dnsmasq:
  file.managed:
    - name: /etc/dnsmasq.d/lxc
    - source: salt://makina-states/files/etc/dnsmasq.d/lxc
    - mode: 750
    - user: root
    - group: root
    - require_in:
      - service: lxc-dnsmasq
  service.running:
    - name: dnsmasq
    - enable: True
    - enable: True
    - require_in:
      - service: lxc-services-enabling

etc-default-lxc:
  file.managed:
    - name: /etc/default/lxc
    - source: salt://makina-states/files/etc/default/lxc
    - user: root
    - group: root
    - require_in:
      - service: lxc-dnsmasq
      - service: lxc-services-enabling

lxc-mount-cgroup:
  mount.mounted:
    - name: /sys/fs/cgroup
    - device: none
    - fstype: cgroup
    - mkmnt: True
    - opts:
      - defaults
    - require_in:
      - service: lxc-services-enabling

etc-init.d-lxc-net:
  file.managed:
    - name: /etc/init.d/lxc-net
    - source: salt://makina-states/files/etc/init.d/lxc-net.sh
    - mode: 750
    - user: root
    - group: root
    - require_in:
      - service: lxc-services-enabling

c-/etc/apparmor.d/lxc/lxc-default:
  file.managed:
    - name: /etc/apparmor.d/lxc/lxc-default
    - source: salt://makina-states/files/etc/apparmor.d/lxc/lxc-default
    - makedirs: true
    - mode: 644
    - user: root
    - group: root
    - require_in:
      - service: lxc-services-enabling
      - service: lxc-apparmor

lxc-apparmor:
  service.running:
    - name: apparmor
    - reload: true
    - enable: true
    - watch:
      - file: c-/etc/apparmor.d/lxc/lxc-default
    - require_in:
      - service: lxc-services-enabling
{% endif %}

lxc-services-enabling:
  service.running:
    - enable: True
    - names:
      - lxc
      - lxc-net
      - lxc-net-makina
    - require_in:
      - mc_proxy: lxc-post-inst
    {% if full %}
    - require:
      - pkg: lxc-pkgs
    {% endif %}
{#-
# as it is often a mount -bind, we must ensure we can attach dependencies there
# set in pillar:
# makina-states.localsettings.lxc_root: real dest
# #}
{%- set lxc_root = locs.var_lib_dir+'/lxc' %}
{%- set lxc_bindmounted_orig_dir = locs.lxc_root %}
lxc-root:
  file.directory:
    - name: {{ lxc_root }}
    - require_in:
      - mc_proxy: lxc-post-inst

{% if lxc_bindmounted_orig_dir -%}
lxc-dir:
  file.directory:
    - name: {{ lxc_bindmounted_orig_dir }}
    - require_in:
      - mc_proxy: lxc-post-inst

lxc-mount:
  mount.mounted:
    - require:
      - file: lxc-dir
    - name: {{ lxc_root }}
    - device: {{ lxc_bindmounted_orig_dir }}
    - fstype: none
    - mkmnt: True
    - opts: bind
    - require:
      - file: lxc-root
      - file: lxc-dir
    - require_in:
      - mc_proxy: lxc-post-inst
      - file: lxc-after-maybe-bind-root
{% endif %}
lxc-after-maybe-bind-root:
  file.directory:
    - name: {{ locs.var_lib_dir }}/lxc
    - require_in:
      - mc_proxy: lxc-post-inst
    - require:
      - file: lxc-root
{% endmacro %}
{{ do(full=False) }}
