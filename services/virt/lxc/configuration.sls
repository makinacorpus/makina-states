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
{%- set localsettings = salt['mc_localsettings.settings']() %}
include:
  - makina-states.services.virt.lxc.hooks

{% if grains['os'] in ['Ubuntu'] -%}
etc-init-lxcconf:
  file.managed:
    - name: /etc/init/lxc.conf
    - source: salt://makina-states/files/etc/init/lxc.conf
    - mode: 750
    - user: root
    - group: root
    - watch:
      - mc_proxy: lxc-pre-conf
    - watch_in:
      - mc_proxy: lxc-post-conf
{% endif %}
{% if grains['os'] in ['Debian'] -%}
lxc-ubuntu-template:
  file.managed:
    - name: /usr/share/lxc/templates/lxc-ubuntu
    - source: salt://makina-states/files/usr/share/lxc/templates/lxc-ubuntu
    - mode: 750
    - user: root
    - group: root
    - watch:
      - mc_proxy: lxc-pre-conf
    - watch_in:
      - mc_proxy: lxc-post-conf

lxc-dnsmasq:
  file.managed:
    - name: /etc/dnsmasq.d/lxc
    - source: salt://makina-states/files/etc/dnsmasq.d/lxc
    - mode: 750
    - user: root
    - group: root
    - watch:
      - mc_proxy: lxc-pre-conf
    - watch_in:
      - mc_proxy: lxc-post-conf

etc-default-lxc:
  file.managed:
    - name: /etc/default/lxc
    - source: salt://makina-states/files/etc/default/lxc
    - user: root
    - group: root
    - watch:
      - mc_proxy: lxc-pre-conf
    - watch_in:
      - mc_proxy: lxc-post-conf

lxc-mount-cgroup:
  mount.mounted:
    - name: /sys/fs/cgroup
    - device: none
    - fstype: cgroup
    - mkmnt: True
    - opts:
      - defaults
    - watch:
      - mc_proxy: lxc-pre-conf
    - watch_in:
      - mc_proxy: lxc-post-conf

etc-init.d-lxc-net:
  file.managed:
    - name: /etc/init.d/lxc-net
    - source: salt://makina-states/files/etc/init.d/lxc-net.sh
    - mode: 750
    - user: root
    - group: root
    - watch:
      - mc_proxy: lxc-pre-conf
    - watch_in:
      - mc_proxy: lxc-post-conf

c-/etc/apparmor.d/lxc/lxc-default:
  file.managed:
    - name: /etc/apparmor.d/lxc/lxc-default
    - source: salt://makina-states/files/etc/apparmor.d/lxc/lxc-default
    - makedirs: true
    - mode: 644
    - user: root
    - group: root
    - watch:
      - mc_proxy: lxc-pre-conf
    - watch_in:
      - mc_proxy: lxc-post-conf
{% endif %}
