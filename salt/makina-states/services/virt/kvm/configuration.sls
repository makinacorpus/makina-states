{#-
# define in pillar an entry "*-kvm-container-def
# as:
# toto-kvm-container-def:
#  name: theservername (opt, take "toto" as servername otherwise)
#  mac: 00:16:3e:04:60:bd
#  ip4: 10.0.3.2
#  netmask: 255.255.255.0 (opt)
#  gateway: 10.0.3.1 (opt)
#  dnsservers: 10.0.3.1 (opt)
#  template: ubuntu (opt)
#  rootfs: root directory (opt)
#  config: config path (opt)
# and it will create an ubuntu templated kvm host
#}
include:
  - makina-states.services.virt.kvm.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}

{% if grains['os'] in ['Ubuntu'] -%}
{% endif %}
{% endif %}
