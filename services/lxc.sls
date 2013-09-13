{% set lxc_root = '/var/lib/lxc' %}
# define in pillar an entry "*-lxc-server-def
# as:
# toto-server-def:
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

lxc-pkgs:
  pkg.installed:
    - names:
      - lxc
      - lxctl

lxc-services-enabling:
  service.running:
    - enable: True
    - names:
      - lxc
      - lxc-net

# as it is often a mount -bind, we must ensure we can attach dependencies there
# we must can :
# react before the bind mount
# react after the bind mount
# eg you can define your bind root as follow
# lxc-mount:
#   mount.mounted:
#     - require:
#       - file: lxc-dir
#     - name: /var/lib/lxc
#     - device:  /mnt/data
#     - fstype: none
#     - mkmnt: True
#     - opts: bind
#     - require:
#       - file: lxc-root
#     - require_in:
#       - file: lxc-after-maybe-bind-root
lxc-root:
  file.directory:
    - name: /var/lib/lxc

lxc-after-maybe-bind-root:
  file.directory:
    - name: /var/lib/lxc
  require:
    - file: lxc-root

{% for k, lxc_data in pillar.items() -%}
{% if k.endswith('lxc-server-def')  -%}
{% set lxc_name = lxc_data.get('name', k.split('-lxc-server-def')[0]) -%}
{% set lxc_mac = lxc_data['mac'] -%}
{% set lxc_ip4 = lxc_data['ip4'] -%}
{% set lxc_template = lxc_data.get('template', 'ubuntu') -%}
{% set lxc_netmask = lxc_data.get('netmask', '255.255.255.0') -%}
{% set lxc_gateway = lxc_data.get('gateway', '10.0.3.1') -%}
{% set lxc_dnsservers = lxc_data.get('dnsservers', '10.0.3.1') -%}
{% set lxc_root = lxc_data.get('root', '/var/lib/lxc/' + lxc_name) -%}
{% set lxc_rootfs = lxc_data.get('rootfs', lxc_root + '/rootfs') -%}
{% set lxc_config = lxc_data.get('config', lxc_root + '/config') -%}
{{ lxc_name }}-lxc:
  cmd.script:
    - source: salt://makina-states/_scripts/lxc-init.sh
    - name: /srv/salt/.running-lxc-init.sh
    - args: {{ lxc_name }} {{ lxc_template }}
    - stateful: True
  require:
    - file: lxc-after-maybe-bind-root

{{ lxc_name }}-lxc-salt-pillar:
  file.directory:
    - require:
      - cmd: {{ lxc_name }}-lxc
    - name: {{ lxc_rootfs }}/srv/pillar
    - makedirs: True
    - mode: '0755'
    - user: root
    - group: root

{{ lxc_name }}-lxc-salt:
  file.recurse:
    - name: {{ lxc_rootfs }}/srv/salt/makina-states
    - require:
      - cmd: {{ lxc_name }}-lxc
    - source: salt://makina-states
    - user: root
    - group: root
    - file_mode: '0755'
    - dir_mode: '0755'
    - recurse: True
    - exclude_pat: E@^((bin|src|(develop-)*eggs|parts)\/|\.installed.cfg|.*\.pyc)

{{ lxc_name }}-lxc-config:
  file.managed:
    - require:
      - file: {{ lxc_name }}-lxc-salt
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - name: {{ lxc_config }}
    - lxc_name: {{ lxc_name }}
    - source: salt://makina-states/files/lxc-config
    - macaddr: {{ lxc_mac }}
    - ip4: {{ lxc_ip4 }}

{{ lxc_name }}-lxc-service:
  file.symlink:
    - require:
      - file: {{ lxc_name }}-lxc-config
    - name: /etc/lxc/auto/{{ lxc_name }}.conf
    - target: {{ lxc_config }}
    - require:
      - cmd: {{ lxc_name }}-lxc

{{lxc_name}}-lxc-network-cfg:
  file.managed:
    - name: {{ lxc_rootfs }}/etc/network/interfaces
    - source: salt://makina-states/files/etc/network/interfaces
    - user: root
    - group: root
    - mode: '0644'
    - template: jinja
    - makina_network:
        eth0:
         address: {{ lxc_ip4 }}
         netmask: {{ lxc_netmask }}
         gateway: {{ lxc_gateway }}
         dnsservers: {{ lxc_dnsservers }}

{{ lxc_name }}-lxc-host-host:
  file.append:
    - require_in:
      - cmd: start-{{ lxc_name }}-lxc-service
    - name: {{ lxc_rootfs }}/etc/hosts
    - text: {{ lxc_gateway }} {{ grains.get('fqdn') }}

{{ lxc_name }}-lxc-host-guest:
  file.append:
    - require_in:
      - cmd: start-{{ lxc_name }}-lxc-service
    - name: {{ lxc_rootfs }}/etc/hosts
    - text: {{ lxc_ip4 }} {{ lxc_name }}

start-{{ lxc_name }}-lxc-service:
  cmd.run:
    - require:
      - cmd: {{ lxc_name }}-lxc
      - file: {{lxc_name}}-lxc-network-cfg
    - name: lxc-start -n {{ lxc_name }} -d && echo changed=false

{% set makinahosts=[] -%}
{% for k, data in pillar.items() -%}
{% if k.endswith('makina-hosts') -%}
{% set dummy=makinahosts.extend(data) -%}
{% endif -%}
{% endfor -%}
{% for host in makinahosts -%}
{% if host['ip'] == '127.0.0.1' -%}
lxc-{{ lxc_name }}{{ host['ip'].replace('.', '_') }}-{{ host['hosts'].replace(' ', '_') }}-host:
  file.append:
    - require:
      - cmd: {{ lxc_name }}-lxc
    - name: {{ lxc_rootfs }}/etc/hosts
    - text: {{ lxc_gateway }} {{ host['hosts'] }}
{% endif %}
{% endfor %}

bootstrap-salt-in-{{ lxc_name }}-lxc:
  cmd.script:
    - source: salt://makina-states/_scripts/lxc-salt.sh
    - args: {{ lxc_name }} server
    - stateful: True
    - require:
      - file: {{ lxc_name }}-lxc-salt
      - cmd: start-{{ lxc_name }}-lxc-service
{% endif -%}
{%- endfor %}
