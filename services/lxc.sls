{% import 'makina-states/services/pkgs.sls'  as pkgs with context %}
include:
  - makina-states.services.pkgs

{% set lxc_root = '/var/lib/lxc' %}
{% set lxc_dir = pillar.get('lxc.directory', '') %}
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
#  salt_bootstrap: bootstrap state to use in salt default "vm"
#           - vm | standalone | server | mastersalt
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
# set in pillar:
# lxc.directory: real dest

lxc-root:
  file.directory:
    - name: {{lxc_root}}

{% if lxc_dir %}
lxc-dir:
  file.directory:
    - name: {{lxc_dir}}

lxc-mount:
  mount.mounted:
    - require:
      - file: lxc-dir
    - name: {{lxc_root}}
    - device: {{lxc_dir}}
    - fstype: none
    - mkmnt: True
    - opts: bind
    - require:
      - file: lxc-root
      - file: lxc-dir
    - require_in:
      - file: lxc-after-maybe-bind-root
{% endif %}


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
{% set salt_bootstrap = lxc_data.get('salt_bootstrap', 'vm') -%}
{% set lxc_netmask = lxc_data.get('netmask', '255.255.255.0') -%}
{% set lxc_gateway = lxc_data.get('gateway', '10.0.3.1') -%}
{% set lxc_dnsservers = lxc_data.get('dnsservers', '10.0.3.1') -%}
{% set lxc_root = lxc_data.get('root', '/var/lib/lxc/' + lxc_name) -%}
{% set lxc_rootfs = lxc_data.get('rootfs', lxc_root + '/rootfs') -%}
{% set lxc_s = lxc_rootfs + '/srv/salt' %}
{% set salt_init = lxc_s + '/.salt-init.sh' %}
{% set lxc_init = '/srv/salt/.lxc-'+ lxc_name + '.sh' %}
{% set lxc_config = lxc_data.get('config', lxc_root + '/config') -%}
{{ lxc_name }}-lxc:
  file.managed:
    - name: {{lxc_init}}
    - source: salt://makina-states/_scripts/lxc-init.sh
    - mode: 750
  cmd.run:
    - name: {{lxc_init}} {{ lxc_name }} {{ lxc_template }}
    - stateful: True
    {% if lxc_template == 'ubuntu' %}
    - require_in:
      - file: main-repos-updates-{{lxc_name}}
      - file: main-repos-{{lxc_name}}
    {% endif %}
    - require:
      - file: {{ lxc_name }}-lxc
      - file: lxc-after-maybe-bind-root

{{pkgs.set_packages_repos(lxc_rootfs, '-'+lxc_name, update=False)}}

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
  cmd.run:
    - name: |
            rsync -a --numeric-ids /srv/salt/makina-states/ {{ lxc_rootfs }}/srv/salt/makina-states/ --exclude '*.pyc';
            cd {{ lxc_rootfs }}/srv/salt/makina-states/ && rm -rf bin src develop-eggs eggs parts .installed.cfg
    - unless: ls -d {{ lxc_rootfs }}/srv/salt/makina-states/src/salt
    - require:
      - cmd: {{ lxc_name }}-lxc
      - pkg: sys-pkgs

{{ lxc_name }}-lxc-config:
  file.managed:
    - require:
      - cmd: {{ lxc_name }}-lxc-salt
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
    - context:
      makina_network:
        eth0:
          address: {{ lxc_ip4 }}
          netmask: {{ lxc_netmask }}
          gateway: {{ lxc_gateway }}
          dnsservers: {{ lxc_dnsservers }}

# {{ lxc_rootfs }}/etc/hosts block entry mangment, collecting
# data from accumulated states and pushing that in the hosts file
#
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

# Add DNS record in lxc guest's /etc/hosts
# record fqdn names of the lxc host
# with the gateway IP
#
# This states will use an accumulator to build the dynamic block content in {{ lxc_rootfs }}/etc/hosts
# (@see {{ lxc_name }}-lxc-hosts-block)
{{ lxc_name }}-lxc-hosts-host:
  file.accumulated:
    - filename: {{ lxc_rootfs }}/etc/hosts
    - name: lxc-hosts-accumulator-entries
    - text: "{{ lxc_gateway }} {{ grains.get('fqdn') }}"
    - require_in:
      - file: {{ lxc_name }}-lxc-hosts-block

# Add entries on lxc guests's /etc/hosts with
# lxc_name and related IP on the lxc netxwork
#
# This states will use an accumulator to build the dynamic block content in {{ lxc_rootfs }}/etc/hosts
# (@see {{ lxc_name }}-lxc-hosts-block)
{{ lxc_name }}-lxc-hosts-guest:
  file.accumulated:
    - filename: {{ lxc_rootfs }}/etc/hosts
    - name: lxc-hosts-accumulator-entries
    - text: "{{ lxc_ip4 }} {{ lxc_name }}"
    - require_in:
      - file: {{ lxc_name }}-lxc-hosts-block
      - cmd: start-{{ lxc_name }}-lxc-service

start-{{ lxc_name }}-lxc-service:
  cmd.run:
    - require:
      - cmd: {{ lxc_name }}-lxc
      - file: {{lxc_name}}-lxc-network-cfg
    - name: lxc-start -n {{ lxc_name }} -d && echo changed=false

{% set makinahosts=[] -%}
{% set hosts_list=[] %}
{% for k, data in pillar.items() -%}
{% if k.endswith('makina-hosts') -%}
{% set dummy=makinahosts.extend(data) -%}
{% endif -%}
{% endfor -%}

# loop to create a dynamic list of hosts based on pillar content
# Adding hosts records, similar as the ones explained in servers.hosts state
# But only recording the one using 127.0.0.1 (the lxc host loopback)
{% for host in makinahosts %}
### For localhost entries, replace with the lxc getway ip
{% if host['ip'] == '127.0.0.1' -%}
  {% set dummy=hosts_list.append( lxc_gateway + ' ' + host['hosts'] ) %}
### Else replicate them into the HOSTS of the container
{% else %}
  {% set dummy=hosts_list.append( host['ip'] + ' ' + host['hosts'] ) %}
{% endif %}
{% endfor %}
{% if hosts_list %}
# spaces are used in the join operation to make this text looks like a yaml multiline text
{% set separator="\n        "%}
# this state use an accumulator to store all pillar names found
# you can reuse this accumulator on other states
# if you want to add content to the block handled by
# {{ lxc_name }}-lxc-hosts-guest
lxc-{{ lxc_name }}-pillar-localhost-host:
  file.accumulated:
    - filename: {{ lxc_rootfs }}/etc/hosts
    - name: lxc-hosts-accumulator-entries
    - text: |
        {{ hosts_list|sort|join(separator) }}
    - require_in:
      - file: {{ lxc_name }}-lxc-hosts-block
    - require:
      - cmd: {{ lxc_name }}-lxc
{% endif %}

bootstrap-salt-in-{{ lxc_name }}-lxc:
  file.managed:
    - name: {{salt_init}}
    - source: salt://makina-states/_scripts/lxc-salt.sh
    - mode: 750
  cmd.run:
    - name: {{salt_init}} {{ lxc_name }} {{ salt_bootstrap }}
    - stateful: True
    - require:
      {% if lxc_template == 'ubuntu' %}
      - file: main-repos-updates-{{lxc_name}}
      - file: main-repos-{{lxc_name}}
      {% endif %}
      - file: bootstrap-salt-in-{{ lxc_name }}-lxc
      - cmd: {{ lxc_name }}-lxc-salt
      - cmd: start-{{ lxc_name }}-lxc-service
{% endif -%}
{%- endfor %}
