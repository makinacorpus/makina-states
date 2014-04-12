{{ salt['mc_macros.register']('services', 'dns.bind') }}
{% set settings = salt['mc_bind.settings']() %}
{% set yameld_data = settings|yaml %}

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

{% macro install_zone(zone, data) %}
{% if salt['mc_bind.is_valid_zone'](data) %}
dns-rzones-{{zone}}-{{data.fpath}}:
  file.managed:
    {% if data.template %}
    - template: jinja
    {% endif %}
    - name: {{ data.fpath}}
    - source: {{data.source}}
    - user: {{settings.user}}
    - group: {{settings.group}}
    - mode: {{settings.mode}}
    - makedirs: true
    - defaults:
      view: |
            {{salt['mc_utils.json_dump'](data['views'])}}
      zdata: |
             {{salt['mc_utils.json_dump'](data)}}
    - watch:
      - mc_proxy: bind-pre-conf
    - watch_in:
      - mc_proxy: bind-post-conf

bind-checkconf-{{zone}}-{{data.fpath}}:
  cmd.watch:
    - name: named-checkzone {{zone}} {{data.fpath}}
    {# do not trigger reload but report problems #}
    - unless: named-checkzone {{zone}} {{data.fpath}}
    - user: root
    - watch:
      - mc_proxy: bind-post-conf
    - watch_in:
      - mc_proxy: bind-check-conf
{% endif %}

{#
{% if data.dnssec %}
signed-{{file}}:
  cmd.run:
    - cwd: {{ settings.named_directory }}
    - name: zonesigner -zone {{ key }} {{ file }}
    - prereq:
      - file: zones-{{ file }}
      {% endif %}
{% endif %}
#}
{% endmacro %}

{% macro do(full=True) %}
include:
  - makina-states.services.dns.bind-hooks

{% if full %}
bind-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs: {{settings.pkgs}}
    - watch:
      - mc_proxy: bind-pre-install
    - watch_in:
      - mc_proxy: bind-post-install

{% endif %}
bind-dirs:
  file.directory:
    - names: |
             {{salt['mc_utils.json_dump'](settings.extra_dirs)}}
    - makedirs: true
    - user: root
    - group: bind
    - mode: 775
    - watch_in:
      - mc_proxy: bind-pre-conf
    - watch:
      - mc_proxy: bind-post-install

bind-/var/log/bind9:
  file.directory:
    - name: {{settings.log_dir}}
    - user: root
    - group: bind
    - mode: 775
    - watch_in:
      - mc_proxy: bind-pre-conf
    - watch:
      - mc_proxy: bind-post-install

named_directory:
  file.directory:
    - name: {{ settings.named_directory }}
    - user: {{settings.user}}
    - group: {{settings.group}}
    - mode: 775
    - makedirs: True
    - watch:
      - mc_proxy: bind-post-install
    - watch_in:
      - mc_proxy: bind-pre-conf

{% for tp in ['bind',
              'local',
              'key',
              'logging',
              'default_zones',
              'options',
              'acl',
              'servers',
              'views'] %}
bind_config_{{tp}}:
  file.managed:
    - name: {{ settings['{0}_config'.format(tp)]}}
    - source: {{settings['{0}_config_template'.format(tp)]}}
    - template: jinja
    - user: {{settings.user}}
    - group: {{settings.group}}
    - mode: {{settings.mode}}
    - defaults:
      data: {{yameld_data}}
    - watch:
      - mc_proxy: bind-pre-conf
    - watch_in:
      - mc_proxy: bind-post-conf
{% endfor %}


rndc-key:
  cmd.run:
    - name: rndc-confgen -r /dev/urandom -a -c {{settings.rndc_key}}
    - unless: test -e {{settings.rndc_key}}
    - user: root
    - watch:
      - mc_proxy: bind-post-install
    - watch_in:
      - mc_proxy: bind-pre-conf
  file.managed:
    - name: {{settings.rndc_key}}
    - mode: 660
    - user: {{settings.user}}
    - group: {{settings.group}}
    - watch:
      - cmd: rndc-key
      - mc_proxy: bind-post-install
    - watch_in:
      - mc_proxy: bind-pre-conf

bind_config_rndc:
  file.managed:
    - name: {{settings.rndc_conf}}
    - source: {{settings.rndc_config_template}}
    - template: jinja
    - user: {{settings.user}}
    - group: {{settings.group}}
    - mode: {{settings.mode}}
    - defaults: {{yameld_data}}
    - watch:
      - mc_proxy: bind-pre-conf
    - watch_in:
      - mc_proxy: bind-post-conf

{% for typ in settings.zone_kinds %}
{% for zone, data in settings[typ].items() %}
{# deactivated in favor of powerdns
{{ install_zone(zone, data) }}
#}
{% endfor %}
{% endfor %}

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
{{ switch_dns(
  suf='postbindrestart',
  require_in=['mc_proxy: bind-post-end'],
  require=['mc_proxy: bind-post-restart'],
  dnsservers=['127.0.0.1'] + settings.default_dnses) }}
{% endmacro %}
{{ do(full=False) }}
