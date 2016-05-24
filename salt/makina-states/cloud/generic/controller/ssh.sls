{% set cloudSettings = salt['mc_cloud.settings']() %}
include:
  - makina-states.localsettings.sshkeys
  - makina-states.services.base.ssh.rootkey

saltcloud-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - sshpass

{% set f = '/root/.ssh/config' %}
{% set settings = salt['mc_cloud_controller.settings']() %}
{% for host, hdata in settings.compute_nodes.items() %}
{% for vm, vmdata in hdata.get('vms', {}).items() %}
{% set extpillar = salt['mc_cloud_vm.vm_extpillar'](vm) %}
{% set port = salt['mc_cloud_compute_node.get_ssh_port'](vm, target=host) %}
{% if extpillar.get('additional_ips', None) %}{% set port = '22' %}{% endif %}
{% if 'lxc' == vmdata.vt %}
prepend-mccloud-{{host}}{{vm}}-sshconfig:
  file.accumulated:
    - require_in:
      - file: mclcoud-{{host}}{{vm}}-sshconfig
    - filename: {{f}}
    - text: |
            Host {{vm}}
            Port {{port}}
            User root
            ServerAliveInterval 5

mclcoud-{{host}}{{vm}}-sshconfig:
  file.blockreplace:
    - name: {{f}}
    - marker_start: "#-- start ssh mapping for {{vm}}"
    - marker_end: "#-- end ssh mapping for {{vm}}"
    - content: ''
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
{%endif %}
{%endfor %}
{%endfor %}
