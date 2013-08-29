#
# Configure /etc/hosts entries based on pillar informations
# eg in pillar:
# toto-makina-hosts:
#   - ip: 127.0.0.1
#     hosts: foo foo.company.com
#
{% set makinahosts=[] %}
{% for k, data in pillar.items() %}
{% if k.endswith('makina-hosts') %}
{% set dummy=makinahosts.extend(data) %}
{% endif %}
{% endfor %}
{% for host in makinahosts %}
{{ host['ip'].replace('.', '_') }}-{{ host['hosts'].replace(' ', '_') }}-host:
  file.append:
    - name: /etc/hosts
    - text: {{ host['ip'] }} {{ host['hosts'] }}
{% endfor %}
