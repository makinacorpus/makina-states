{% set data = salt['mc_cloud_compute_node.settings']() %}
{% set vmdata = salt['mc_cloud_vm.settings']() %}
include:
  - makina-states.services.firewall.firewall
  - makina-states.services.virt.kvm

{% if grains['os'] not in ['Ubuntu'] %}
{% endif %}

{% set kvmSettings =  vmdata.vts.kvm %}
kvm-noop:
  mc_proxy.hook: []

{% for tdata in kvmSettings.defaults.get('pools', []) %}
{% set i = tdata.name %}
{% if tdata.get('type') == 'lvm' %}
# only define if vg exists and vg is not an active
# libvirt pool
kvm-volume-exists-{{i}}:
  cmd.run:
    - name: test "x$(vgs --all --noheadings|awk '{print $1}'|egrep '^{{i}}$'|head -n1)" = "x{{i}}"
    - onlyif: test "x$(vgs --all --noheadings|awk '{print $1}'|egrep '^{{i}}$'|head -n1)" != "x{{i}}"
    - watch:
      - mc_proxy: kvm-post-inst

kvm-define-pool-{{i}}:
  cmd.run:
    - onlyif: test "x$(virsh pool-list --all|sed  -e '1,2d'|awk '{print $1}'|egrep '^{{i}}$'|head -n1)" != "x{{i}}"
    - name: virsh pool-define-as "{{i}}" logical --target "/dev/{{i}}"
    - watch:
      - cmd: kvm-volume-exists-{{i}}
      - mc_proxy: kvm-post-inst

kvm-start-pool-{{i}}:
  cmd.run:
    - onlyif: test "x$(virsh pool-list --all --details|awk '{print $1}'|egrep -q '^{{i}}';echo ${?})" = "x0" && test "x$(LC_ALL=C virsh pool-list --details|egrep "^[ ]*{{i}} .*"|head -n 1|awk '{print $2}')" != "xrunning"
    - name: virsh pool-start {{i}}
    - watch:
      - mc_proxy: kvm-post-inst
      - cmd: kvm-define-pool-{{i}}
kvm-autostart-pool-{{i}}:
  cmd.run:
    - onlyif: test "x$(virsh pool-list --all --details|awk '{print $1}'|egrep -q '^{{i}}';echo ${?})" = "x0" && test "x$(LC_ALL=C virsh pool-list --details|egrep "^[ ]*{{i}} .*"|head -n 1|awk '{print $3}')" != "xyes"
    - name: virsh pool-autostart {{i}}
    - watch:
      - mc_proxy: kvm-post-inst
      - cmd: kvm-define-pool-{{i}}
# 95  virsh pool-start vg
# 97  virsh pool-autostart vg
{%endif%}
{% endfor %}
