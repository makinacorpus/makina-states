{% set settings = salt['mc_dhcpd.settings']() %}
{% set yameld_data = salt['mc_utils.json_dump'](settings) %}
{% if salt['mc_controllers.mastersalt_mode']() %}
include:
  - makina-states.services.dns.dhcpd.hooks
  - makina-states.services.dns.dhcpd.services
{% for tp in [ '/etc/default/isc-dhcp-server', ] %}
dhcpd_config_{{tp}}:
  file.managed:
    - name: {{tp}}
    - makedirs: true
    - source: salt://makina-states/files{{tp}}
    - template: jinja
    - mode: 750
    - user: root
    - group: root
    - defaults:
      data: |
            {{yameld_data}}
    - watch:
      - mc_proxy: dhcpd-pre-conf
    - watch_in:
      - mc_proxy: dhcpd-post-conf
{% endfor %}
{% endif%}
