{% import "makina-states/localsettings/dns/macros.sls" as dns with context %}
{% set settings = salt['mc_bind.settings']() %}
include:
  - makina-states.services.dns.bind.hooks

{# before restart, be sure switch over to default dns
   which will be available in case of problem #}
{{ dns.switch_dns(suf='prebindstart',
                  require=['mc_proxy: bind-check-conf'],
                  require_in=['mc_proxy: bind-pre-restart']) }}

bind-checkconf:
  cmd.run:
    - name: named-checkconf
    - unless: named-checkconf
    {# do not trigger reload but report problems #}
    - user: root
    - watch:
      - mc_proxy: bind-post-conf
    - watch_in:
      - mc_proxy: bind-check-conf

{% if grains['os'] in ['Ubuntu'] %}
bind-deactivate-dnsmask:
  cmd.run:
    - name: |
            service dnsmasq stop;
            update-rc.d -f dnsmasq remove;
            if [ -e /etc/NetworkManager/NetworkManager.conf ];then
              sed -i -e "s/^dns=dnsmasq/#dns=dnsmasq/g" /etc/NetworkManager/NetworkManager.conf;
            fi;
            if [ -e /etc/default/dnsmasq ];then
              sed -i -e "s/^ENABLED.*/ENABLED=0/g" /etc/default/dnsmasq;
            fi;
            /bin/true;
    - onlyif: egrep -q "^ENABLED=1" /etc/default/dnsmasq
    - watch:
      - mc_proxy: bind-pre-conf
    - watch_in:
      - service: bind-service-reload
      - service: bind-service-restart
{% endif %}

bind-service-restart:
  service.running:
    - name: {{settings.service_name}}
    - enable: True
    - watch:
      - mc_proxy: bind-pre-restart
    - watch_in:
      - mc_proxy: bind-post-restart

{% if grains['os'] in ['Ubuntu'] %}
apparmor-bind-service-reload:
  cmd.watch:
    - name: service apparmor restart
    - watch:
      - mc_proxy: bind-pre-reload
    - watch_in:
      - mc_proxy: bind-post-reload
{% endif %}

bind-service-reload:
  service.running:
    - name: {{settings.service_name}}
    - enable: True
    - reload: True
    - watch:
      - mc_proxy: bind-pre-reload
    - watch_in:
      - mc_proxy: bind-post-reload

{# be sure to have the resolvconf well configured, over, & over #}
{{ dns.switch_dns(suf='postbindrestart',
                  require_in=['mc_proxy: bind-post-end'],
                  require=['mc_proxy: bind-post-restart']) }}
