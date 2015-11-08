{% set pkgssettings = salt['mc_pkgs.settings']() %}
{% set settings = salt['mc_bind.settings']() %}
{% set zones = salt['mc_bind.cached_zone_headers']() %}

{% set checked_zones = {} %}

{% macro install_zone(zone) %}
{% set data = zones[zone] %}
dns-rzones-{{zone}}-{{data.fpath}}:
  file.managed:
    - name: {{ data.fpath}}
    {% if data.server_type == 'slave' %}
    - source: ''
    {% else %}
    {% if data.template %}
    - source: {{data.source}}
    - context:
        zoneid: {{zone}}
    - template: jinja
    {% endif %}
    {% endif %}
    - user: {{settings.zuser}}
    - group: {{settings.group}}
    - mode: {{settings.mode}}
    - makedirs: true
    - watch:
      - mc_proxy: bind-pre-conf
    - watch_in:
      - mc_proxy: bind-post-conf
{% if data.server_type in ['master'] %}
{% if not zone in checked_zones %}
{% do checked_zones.update({zone: data.fpath}) %}
{% endif %}
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

{% if salt['mc_controllers.allow_lowlevel_states']() %}
include:
  - makina-states.services.dns.bind.hooks
  - makina-states.services.dns.bind.services


bind-dirs:
  file.directory:
    - names:
      {% for d in settings.extra_dirs %}
      - "{{d}}"
      {% endfor %}
    - makedirs: true
    - user: bind
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

{% if grains['os'] in ['Ubuntu'] %}
{% for f in ['/etc/apparmor.d/usr.sbin.named'] %}
bind_config_{{f}}:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files{{f}}
    - template: jinja
    - user: root
    - group: root
    - mode: {{settings.mode}}
    - watch:
      - mc_proxy: bind-pre-conf
    - watch_in:
      - mc_proxy: bind-post-conf
{% endfor %}
{% endif %}
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
    - watch:
      - mc_proxy: bind-pre-conf
    - watch_in:
      - mc_proxy: bind-post-conf

{% for zone in settings.zones %}
{{ install_zone(zone) }}
{% endfor %}

bind-checkconf-zones:
  file.managed:
    - name: /etc/bind/checkzones.sh
    - mode: 0755
    - template: jinja
    - source: ''
    - makedirs: true
    - contents: |
                #!/usr/bin/env bash
                ret=0
                domainerrors=""
                {% for zone, fpath in checked_zones.items() %}
                named-checkzone -k fail -m fail -M fail -n fail {{zone}} "{{fpath}}"
                if [ "x${?}" != "x0" ];then
                  ret=1
                  domainerrors="${domainerrors} {{zone}}:{{fpath}}"
                fi
                {% endfor %}
                if [ "x${ret}" = "x0" ];then
                  echo "changed='false'"
                else
                  echo "${domainerrors}"
                  exit ${ret}
                fi
  cmd.run:
    - name: /etc/bind/checkzones.sh
    - stateful: true
    {# do not trigger reload but report problems #}
    - user: root
    - require:
      - file: bind-checkconf-zones
      - mc_proxy: bind-post-conf
    - watch_in:
      - mc_proxy: bind-check-conf
{% endif %}

