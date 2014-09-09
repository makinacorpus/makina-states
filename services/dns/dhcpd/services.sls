{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_dhcpd.settings']() %}
{% set yameld_data = salt['mc_utils.json_dump'](settings) %}

dhcpd-checkconf:
  cmd.run:
    - name: dhcpd -t -cf /etc/dhcp/dhcpd.conf
    - unless: dhcpd -t -cf /etc/dhcp/dhcpd.conf
    {# do not trigger reload but report problems #}
    - user: root
    - watch:
      - mc_proxy: dhcpd-pre-restart
    - watch_in:
      - mc_proxy: dhcpd-post-restart

dhcpd-service-restart:
  service.running:
    - name: {{settings.service_name}}
    - enable: True
    - watch:
      - mc_proxy: dhcpd-pre-restart
    - watch_in:
      - mc_proxy: dhcpd-post-restart

