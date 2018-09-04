{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_dhcpd6.settings']() %}

dhcpd6-checkconf:
  cmd.run:
    - name: dhcpd -6 -t -cf /etc/dhcp/dhcpd6.conf
    - unless: dhcpd -6 -t -cf /etc/dhcp/dhcpd6.conf
    {# do not trigger reload but report problems #}
    - user: root
    - watch:
      - mc_proxy: dhcpd6-pre-restart
    - watch_in:
      - mc_proxy: dhcpd6-post-restart

dhcpd6-service-restart:
  service.running:
    - name: {{settings.service_name}}
    - enable: True
    - watch:
      - mc_proxy: dhcpd6-pre-restart
    - watch_in:
      - mc_proxy: dhcpd6-post-restart

