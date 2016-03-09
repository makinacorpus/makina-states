{%- set locs = salt['mc_locations.settings']() %}
{%- set data = salt['mc_psad.settings']() %}

include:
  - makina-states.services.firewall.psad.services
  - makina-states.services.firewall.psad.hooks

{% for i in [
  'auto_dl',
  'icmp6_types',
  'icmp_types',
  'ip_options',
  'pf.os',
  'posf',
  'protocols',
  'psad.conf',
  'signatures',
  'snort_rule_dl',]%}
makina-etc-psad-{{i}}-conf:
  file.managed:
    - name: {{ locs.conf_dir }}/psad/{{i}}
    - source : salt://makina-states/files/etc/psad/{{i}}
    - makedirs: true
    - template: jinja
    - user: root
    - group: root
    - mode: "0700"
    - defaults:
      data: |
            {{salt['mc_utils.json_dump']( data)}}
    - watch:
      - mc_proxy: psad-pre-conf-hook
    - watch_in:
      - mc_proxy: psad-post-conf-hook
{% endfor %}

