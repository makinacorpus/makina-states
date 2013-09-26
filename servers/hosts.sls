#
# Configure /etc/hosts entries based on pillar informations
# eg in pillar:
#
#toto-makina-hosts:
#    - ip: 10.0.0.8
#      hosts: foo foo.company.com
#    - ip: 10.0.0.3
#      hosts: bar bar.company.com
#others-makina-hosts:
#    - ip: 192.168.1.52.1
#      hosts: foobar foobar.foo.com
#    - ip: 192.168.1.52.2
#      hosts: toto toto.foo.com toto2.foo.com toto3.foo.com
#    - ip: 10.0.0.3
#      hosts: alias alias.foo.com
# If you alter on host IP or if you already used the given hosts string in your /etc/hosts
# this host string will be searched upon the file and removed (the whole line)
# to ensure the same host name is not used with several IPs
{% set makinahosts=[] %}
{% for k, data in pillar.items() %}
{% if k.endswith('makina-hosts') %}
{% set dummy=makinahosts.extend(data) %}
{% endif %}
{% endfor %}
# loop to create a dynamic list of states based on pillar content
{% for host in makinahosts %}
# the state name should not contain dots and spaces
{{ host['ip'].replace('.', '_') }}-{{ host['hosts'].replace(' ', '_') }}-host-cleanup:
  # detect presence of the same host name with another IP
  file.replace:
    - require_in:
      - file: {{ host['ip'].replace('.', '_') }}-{{ host['hosts'].replace(' ', '_') }}-host
    - name: /etc/hosts
    - pattern: ^((?!{{ host['ip'].replace('.', '\.')  }}).)*{{ host['hosts'].replace('.', '\.') }}(.)*$
    - repl: "" 
    - flags: ['IGNORECASE','MULTILINE', 'DOTALL']
    - bufsize: file
    - show_changes: True
# the state name should not contain dots and spaces
{{ host['ip'].replace('.', '_') }}-{{ host['hosts'].replace(' ', '_') }}-host:
    # append new host record
    file.append:
      - name: /etc/hosts
      - text: "{{ host['ip'] }} {{ host['hosts'] }} # entry managed via salt"
{% endfor %}
