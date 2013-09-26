{% import 'makina-states/services/pkgs.sls'  as pkgs with context %}
include:
  - makina-states.services.pkgs

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

{% set lxc_dir = pillar.get('lxc.directory', '') %}
{% set lxc_root = '/var/lib/lxc' %}
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

lxc-root:
  file.directory:
    - name: {{lxc_dir}}

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

# Remove entries on lxc guest's /etc/hosts whith
# host fqdn associated with another IP than the
# gateway IP (if this gateway has moved for example)
{{ lxc_name }}-lxc-host-host-cleanup:
  file.replace:
    - require_in:
      file: {{ lxc_name }}-lxc-host-host
    - name: {{ lxc_rootfs }}/etc/hosts
    # match the domain ( grain fqdn ) on lines not containing the ip ( lxc_gateway )
    - pattern: ^((?!{{ lxc_gateway.replace('.', '\.')  }}).)*{{ grains.get('fqdn').replace('.', '\.') }}(.)*$
    - repl: ""
    - flags: ['IGNORECASE','MULTILINE', 'DOTALL']
    - bufsize: file
    - show_changes: True

# Add DNS record in lxc guest's /etc/hosts
# record fqdn names of the lxc host
# with the gateway IP
#
{{ lxc_name }}-lxc-host-host:
  file.append:
    - require_in:
      - cmd: start-{{ lxc_name }}-lxc-service
    - name: {{ lxc_rootfs }}/etc/hosts
    - text: "{{ lxc_gateway }} {{ grains.get('fqdn') }} # entry managed by salt, lxc host fqdn"

# Remove entries on lxc guests containers's /etc/hosts whith
# lxc_name associated with another IP
#
{{ lxc_name }}-lxc-host-guest-cleanup:
  file.replace:
    - require_in:
      file: {{ lxc_name }}-lxc-host-guest
    - name: {{ lxc_rootfs }}/etc/hosts
    # match the domain ( lxc_name ) on lines not containing the ip ( lxc_ip4 )
    - pattern: ^((?!{{ lxc_ip4.replace('.', '\.')  }}).)*{{ lxc_name.replace('.', '\.') }}(.)*$
    - repl: ""
    - flags: ['IGNORECASE','MULTILINE', 'DOTALL']
    - bufsize: file
    - show_changes: True

# Add entries on lxc guests's /etc/hosts with
# lxc_name and related IP on the lxc netxwork
# network
#
{{ lxc_name }}-lxc-host-guest:
  file.append:
    - require_in:
      - cmd: start-{{ lxc_name }}-lxc-service
    - name: {{ lxc_rootfs }}/etc/hosts
    - text: "{{ lxc_ip4 }} {{ lxc_name }} # entry managed by salt lxc-host detection"

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

# loop to create a dynamic list of states based on pillar content
# Adding hosts records, similar as the ones explained in servers.hosts state
# But only recording the one using 127.0.0.1 (the lxc host loopback)
{% for host in makinahosts -%}
### Manage only refs to localhost
{% if host['ip'] == '127.0.0.1' -%}
# the state name should not contain dots and spaces
{{ host['ip'].replace('.', '_') }}-{{ host['hosts'].replace(' ', '_') }}-lxc-host-cleanup:
  # detect presence of the same host name with another IP
  file.replace:
    - require:
      - cmd: {{ lxc_name }}-lxc
    - require_in:
      - file: {{ host['ip'].replace('.', '_') }}-{{ host['hosts'].replace(' ', '_') }}-host
    - name: {{ lxc_rootfs }}/etc/hosts
    # match the domain ( host['hosts']) on lines not containing the ip (lxc_gateway)
    - pattern: ^((?!{{ lxc_gateway.replace('.', '\.')  }}).)*{{ host['hosts'].replace('.', '\.') }}(.)*$
    - repl: ""
    - flags: ['IGNORECASE','MULTILINE', 'DOTALL']
    - bufsize: file
    - show_changes: True
# the state name should not contain dots and spaces
lxc-{{ lxc_name }}{{ host['ip'].replace('.', '_') }}-{{ host['hosts'].replace(' ', '_') }}-host:
  file.append:
    - require:
      - cmd: {{ lxc_name }}-lxc
    - name: {{ lxc_rootfs }}/etc/hosts
    - text: "{{ lxc_gateway }} {{ host['hosts'] }} # entry managed by salt"
{% endif %}
{% endfor %}

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
      - file: {{ lxc_name }}-lxc-salt
      - cmd: start-{{ lxc_name }}-lxc-service
{% endif -%}
{%- endfor %}
