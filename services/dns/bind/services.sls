{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_bind.settings']() %}
{% set yameld_data = salt['mc_utils.json_dump'](settings) %}
{% macro switch_dns(suf='tmp',
                    require=None,
                    require_in=None,
                    watch=None,
                    watch_in=None,
                    dnsservers=None) %}
{% if not require %}
{% set require = [] %}
{% endif %}
{% if not require_in %}
{% set require_in = [] %}
{% endif %}
{% if not require %}
{% set watch = [] %}
{% endif %}
{% if not watch_in %}
{% set watch_in = [] %}
{% endif %}
{% if not dnsservers %}
{% set dnsservers = settings.default_dnses %}
{% endif %}
{% if not dnsservers %}
{% set dnsservers = ['8.8.8.8', '4.4.4.4'] %}
{% endif %}
bind-set-defaultdns-{{suf}}-1:
  cmd.run:
    - unless: |
              rm /etc/resolv.conf;echo > /etc/resolv.conf;
              {%- for i in dnsservers  %}
              echo "nameserver {{i}}" >> /etc/resolv.conf;
              {% endfor -%}
              /bin/true
    - user: root
    {# only if dnsmask/resolvconf is there #}
    - name: /bin/true
    {% if require_in %}
    - require_in:
      {% for w in require_in %}
      - {{w}}
      {% endfor %}
    {% endif %}
    {% if require %}
    - require:
      {% for w in require %}
      - {{w}}
      {% endfor %}
    {% endif %}
    {% if watch_in %}
    - watch_in:
      {% for w in watch_in %}
      - {{w}}
      {% endfor %}
    {% endif %}
    {% if watch %}
    - watch:
      {% for w in watch %}
      - {{w}}
      {% endfor %}
    {% endif %}

{% if grains['os'] in ['Ubuntu'] %}
bind-set-defaultdns-{{suf}}-2:
  cmd.run:
    - name: /bin/true
    - unless: |
            rm /etc/resolvconf/resolv.conf.d/head;
            echo > /etc/resolvconf/resolv.conf.d/head;
            {%- for i in dnsservers  %}
            echo "nameserver {{i}}" >> /etc/resolvconf/resolv.conf.d/head;
            {% endfor -%}
            service resolvconf restart;
            /bin/true
    - user: root
    {# only if dnsmask/resolvconf is there #}
    {% if require_in %}
    - require_in:
      {% for w in require_in %}
      - {{w}}
      {% endfor %}
    {% endif %}
    - require:
      - cmd: bind-set-defaultdns-{{suf}}-1
      {% for w in require %}
      - {{w}}
      {% endfor %}
    {% if watch_in %}
    - watch_in:
      {% for w in watch_in %}
      - {{w}}
      {% endfor %}
    {% endif %}
    {% if watch %}
    - watch:
      {% for w in watch %}
      - {{w}}
      {% endfor %}
    {% endif %}
{% endif %}
{% endmacro %}
{% if salt['mc_controllers.mastersalt_mode']() %}
include:
  - makina-states.services.dns.bind.hooks

{# before restart, switch over to default dns which will be available in case of problem#}
{{ switch_dns(
  suf='prebindstart',
  require=['mc_proxy: bind-check-conf'],
  require_in=['mc_proxy: bind-pre-restart'],
  dnsservers=settings.default_dnses) }}

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

{# switch back to our shiny new dns server #}
{{ switch_dns(suf='postbindrestart',
              require_in=['mc_proxy: bind-post-end'],
              require=['mc_proxy: bind-post-restart'],
              dnsservers=['127.0.0.1']+settings.default_dnses) }}
{% endif %}
