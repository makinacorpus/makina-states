{% set f = '/root/.ssh/config' %}
{% for id_, tdata in salt['mc_remote_pillar.get_hosts']().items()%}
prepend-mccloud-{{id_}}-sshconfig:
  file.accumulated:
    - require_in:
      - file: mclcoud-{{id_}}-sshconfig
    - filename: {{f}}
    - text: |
            Host {{tdata.ssh_name}}
            HostName {{tdata.ssh_host}}
            Port {{tdata.ssh_port}}
            User {{tdata.ssh_username}}
            ServerAliveInterval 5
            {{salt['mc_cloud.proxy_command'](**tdata)}}

mclcoud-{{id_}}-sshconfig:
  file.blockreplace:
    - name: {{f}}
    - marker_start: "#-- start ssh mapping for {{id_}}"
    - marker_end: "#-- end ssh mapping for {{id_}}"
    - content: ''
    - prepend_if_not_found: True
    - backup: '.bak'
    - show_changes: True
{%endfor%}
