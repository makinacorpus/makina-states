{% set data = salt['mc_cloud_compute_node.cn_settings']() %}
include:
  - makina-states.services.firewall.shorewall
  - makina-states.services.virt.kvm

{% if grains['os'] not in ['Ubuntu'] %}
{% endif %}

{% set kvmSettings =  data.get('kvmSettings', {}) %}
kvm-noop:
  mc_proxy.hook: []

{% for i, tdata in kvmSettings.get('pools', {}).items() %}
{% if tdata.get('type') == 'lvm' %}
# only define if vg exists and vg is not an active
# libvirt pool
kvm-define-pool-{{i}}:
  cmd.run:
    - onlyif: test "x$(vgs --all --noheadings|awk '{print $1}'|egrep '^{{i}}$'|head -n1)" = "x{{i}}" && test "x$(virsh pool-list --all|sed  -e '1,2d'|awk '{print $1}'|egrep '^{{i}}$'|head -n1)" != "x{{i}}"
    - name: virsh pool-define-as "{{i}}" logical --target "/dev/{{i}}"
    - watch:
      - mc_proxy: kvm-post-inst

kvm-start-pool-{{i}}:
  cmd.run:
    - onlyif: test "x$(virsh pool-list --details|awk '{print $1}'|egrep -q '^v{{i}}';echo ${?})" = "x0" && test "x$(LC_ALL=C virsh pool-list --details|egrep "^[ ]*{{i}} .*"|head -n 1|awk '{print $2}')" != "xrunning"
    - name: virsh pool-start {{i}}
    - watch:
      - mc_proxy: kvm-post-inst
      - cmd: kvm-define-pool-{{i}}
kvm-autostart-pool-{{i}}:
  cmd.run:
    - onlyif: test "x$(virsh pool-list --details|awk '{print $1}'|egrep -q '^{{i}}';echo ${?})" = "x0" && test "x$(LC_ALL=C virsh pool-list --details|egrep "^[ ]*{{i}} .*"|head -n 1|awk '{print $3}')" != "xyes"
    - name: virsh pool-autostart {{i}}
    - watch:
      - mc_proxy: kvm-post-inst
      - cmd: kvm-define-pool-{{i}}
# 95  virsh pool-start vg
# 97  virsh pool-autostart vg
{%endif%}
{% endfor %}
