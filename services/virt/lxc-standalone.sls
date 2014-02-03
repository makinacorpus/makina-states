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
{%- import "makina-states/_macros/services.jinja" as services with context %}
{{ salt['mc_macros.register']('services', 'virt.lxc') }}
{%- set localsettings = services.localsettings %}
{%- set locs = localsettings.locations %}
{% macro do(full=True) %}

include:
  - makina-states.services.virt.lxc-hooks

{% if full %}
lxc-pkgs:
  pkg.installed:
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

{% endif %}

lxc-services-enabling:
  service.running:
    - enable: True
    - names:
      - lxc
      - lxc-net
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
{%- set lxc_dir = locs.lxc_root %}

lxc-root:
  file.directory:
    - name: {{ lxc_root }}
    - require_in:
      - mc_proxy: lxc-post-inst

{% if lxc_dir -%}
lxc-dir:
  file.directory:
    - name: {{ lxc_dir }}
    - require_in:
      - mc_proxy: lxc-post-inst

lxc-mount:
  mount.mounted:
    - require:
      - file: lxc-dir
    - name: {{ lxc_root }}
    - device: {{ lxc_dir }}
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

{% for k, lxc_data in services.lxcSettings.containers.items() -%}
{%    set lxc_name = k %}
{%    set lxc_mac = lxc_data['mac'] -%}
{%    set lxc_ip4 = lxc_data['ip4'] -%}
{%    set lxc_template = lxc_data.get('template') -%}
{%    set lxc_netmask = lxc_data.get('netmask') -%}
{%    set lxc_gateway = lxc_data.get('gateway') -%}
{%    set lxc_dnsservers = lxc_data.get('dnsservers') -%}
{%    set lxc_root = lxc_data.get('root') -%}
{%    set lxc_rootfs = lxc_data.get('rootfs') -%}
{%    set lxc_config = lxc_data.get('config') -%}
{%    set lxc_init = locs.tmp_dir+'/.lxc-'+ lxc_name + '.sh' %}
{{ lxc_name }}-lxc:
  file.managed:
    - name: {{ lxc_init }}
    - source: salt://makina-states/_scripts/lxc-init.sh
    - mode: 750
  cmd.run:
    - name: {{ lxc_init }} {{ lxc_name }} {{ lxc_template }}
    - stateful: True
    - require:
      - file: {{ lxc_name }}-lxc
      - file: lxc-after-maybe-bind-root
      {% if full %}
      - pkg: lxc-pkgs
      {% endif %}
    - require_in:
      - mc_proxy: lxc-post-inst

{{ lxc_name }}-lxc-config:
  file.managed:
    - require:
      - cmd: {{ lxc_name }}-lxc
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - name: {{ lxc_config }}
    - lxc_name: {{ lxc_name }}
    - source: salt://makina-states/files/lxc-config
    - macaddr: {{ lxc_mac }}
    - ip4: {{ lxc_ip4 }}
    - require_in:
      - mc_proxy: lxc-post-inst

{{ lxc_name }}-lxc-service:
  file.symlink:
    - require:
      - file: {{ lxc_name }}-lxc-config
    - name: /etc/lxc/auto/{{ lxc_name }}.conf
    - target: {{ lxc_config }}
    - require:
      - cmd: {{ lxc_name }}-lxc
    - require_in:
      - mc_proxy: lxc-post-inst

{{ lxc_name }}-lxc-network-cfg:
  file.managed:
    - require:
      - cmd: {{ lxc_name }}-lxc
    - name: {{ lxc_rootfs }}/etc/network/interfaces
    - source: salt://makina-states/files/etc/network/interfaces
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - context:
      network_interfaces:
        eth0:
          address: {{ lxc_ip4 }}
          netmask: {{ lxc_netmask }}
          gateway: {{ lxc_gateway }}
          dnsservers: {{ lxc_dnsservers }}
{#-
# {{ lxc_rootfs }}/etc/hosts block entry mangment, collecting
# data from accumulated states and pushing that in the hosts file
#}
{{ lxc_name }}-lxc-hosts-block:
  file.blockreplace:
    - name: {{ lxc_rootfs }}/etc/hosts
    - marker_start: "#-- start salt lxc managed zone -- PLEASE, DO NOT EDIT"
    - marker_end: "#-- end salt lxc managed zone --"
    - content: ''
    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True
    - require_in:
      - cmd: start-{{ lxc_name }}-lxc-service
    - require:
      - cmd: {{ lxc_name }}-lxc

{#-
# Add DNS record in lxc guest's /etc/hosts
# record fqdn names of the lxc host
# with the gateway IP
#
# This states will use an accumulator to build the dynamic block content in {{ lxc_rootfs }}/etc/hosts
# (@see {{ lxc_name }}-lxc-hosts-block)
#}
{{ lxc_name }}-lxc-hosts-host:
  file.accumulated:
    - filename: {{ lxc_rootfs }}/etc/hosts
    - name: lxc-hosts-accumulator-entries
    - text: "{{ lxc_gateway }} {{ grains.get('fqdn') }}"
    - require_in:
      - file: {{ lxc_name }}-lxc-hosts-block
{#-
# Add entries on lxc guests's /etc/hosts with
# lxc_name and related IP on the lxc netxwork
#
# This states will use an accumulator to build the dynamic block content in {{ lxc_rootfs }}/etc/hosts
# (@see {{ lxc_name }}-lxc-hosts-block)
#}
{{ lxc_name }}-lxc-hosts-guest:
  file.accumulated:
    - filename: {{ lxc_rootfs }}/etc/hosts
    - name: lxc-hosts-accumulator-entries
    - text: "{{ lxc_ip4 }} {{ lxc_name }}"
    - require_in:
      - file: {{ lxc_name }}-lxc-hosts-block
      - cmd: start-{{ lxc_name }}-lxc-service
      - mc_proxy: lxc-post-inst

start-{{ lxc_name }}-lxc-service:
  cmd.run:
    - require_in:
      - mc_proxy: lxc-post-inst
    - require:
      {% if full %}
      - pkg: lxc-pkgs
      {% endif %}
      - cmd: {{ lxc_name }}-lxc
      - file: {{ lxc_name }}-lxc-network-cfg
    - name: lxc-start -n {{ lxc_name }} -d && echo changed=false
{%    set makinahosts=[] -%}
{%    set hosts_list=[] %}
{%    for k, data in pillar.items() -%}
{%      if k.endswith('makina-hosts') -%}
{%       do makinahosts.extend(data) -%}
{%      endif -%}
{%    endfor -%}
{#-
# loop to create a dynamic list of hosts based on pillar content
# Adding hosts records, similar as the ones explained in localsettings.hosts state
# But only recording the one using 127.0.0.1 (the lxc host loopback)
#}
{% for host in makinahosts %}
{#- ## For localhost entries, replace with the lxc getway ip #}
{% if host['ip'] == '127.0.0.1' -%}
  {% do hosts_list.append( lxc_gateway + ' ' + host['hosts'] ) %}
{# - ## Else replicate them into the HOSTS of the container #}
{% else %}
  {% do hosts_list.append( host['ip'] + ' ' + host['hosts'] ) %}
{% endif %}
{% endfor %}
{% if hosts_list %}
{#- spaces are used in the join operation to make this text looks like a yaml multiline text #}
{% set separator="\n        "%}
{#- this state use an accumulator to store all pillar names found
# you can reuse this accumulator on other states
# if you want to add content to the block handled by
# {{ lxc_name }}-lxc-hosts-guest
#}
lxc-{{ lxc_name }}-pillar-localhost-host:
  file.accumulated:
    - filename: {{ lxc_rootfs }}/etc/hosts
    - name: lxc-hosts-accumulator-entries
    - text: |
        {{ hosts_list|sort|join(separator) }}
    - require_in:
      - mc_proxy: lxc-post-inst
      - file: {{ lxc_name }}-lxc-hosts-block
    - require:
      - cmd: {{ lxc_name }}-lxc
{%      endif %}
{%- endfor %}
{% endmacro %}
{{ do(full=False) }}
