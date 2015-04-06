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
{%- set vmdata = salt['mc_cloud_vm.settings']() %}
{%- set data = vmdata.vts.lxc %}
{% set extra_confs = {} %}
include:
  - makina-states.services.virt.lxc.hooks


{% if salt['mc_controllers.mastersalt_mode']() %}
{% if grains['os'] in ['Ubuntu'] -%}
{% set extra_confs = {
  '/etc/init/lxc-net-makina.conf': {},
} %}

{% elif grains['os'] in ['Debian'] -%}
{% set extra_confs = {'/etc/init.d/lxc-net-makina': {}} %}

# assume systemd 
{% else %}
{% set extra_confs = {'/etc/systemd/system/lxc-net-makina': {}} %}
{% endif%}

{% set extra_confs = salt['mc_utils.copy_dictupdate'](
  data['host_confs'], extra_confs) %}

{% for f, fdata in extra_confs.items() %}
{% set template = fdata.get('template', 'jinja') %}
lxc-conf-{{f}}:
  file.managed:
    - name: "{{fdata.get('target', f)}}"
    - source: "{{fdata.get('source', 'salt://makina-states/files'+f)}}"
    - mode: "{{fdata.get('mode', 750)}}"
    - user: "{{fdata.get('user', 'root')}}"
    - group:  "{{fdata.get('group', 'root')}}"
    {% if template %}
    - template: "{{template}}"
    {%endif%}
    - watch:
      - mc_proxy: lxc-pre-conf
    - watch_in:
      - mc_proxy: lxc-post-conf
{% endfor %}

{% if grains['os'] in ['Debian'] -%}
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
{% endif %}
{% endif %}
