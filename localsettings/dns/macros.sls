{% set settings = salt['mc_dns.settings']() %}
{% macro switch_dns(suf='localsettings',
                    require=None,
                    require_in=None,
                    watch=None,
                    watch_in=None,
                    dnsservers=None) %}

{# hooks for dns orchestration #}
ms-dns-pre-{{suf}}:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ms-dns-post-{{suf}}

ms-dns-post-{{suf}}:
  mc_proxy.hook: []

{% if salt['mc_controllers.mastersalt_mode']() %}
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
{% set dnsservers = salt['mc_utils.uniquify'](dnsservers) %}
bind-set-defaultdns-{{suf}}-1:
  cmd.run:
    - unless: |
              {% if salt['mc_controllers.mastersalt_mode']()%}
              rm /etc/resolv.conf;echo > /etc/resolv.conf;
              {%- for i in dnsservers  %}
              echo "nameserver {{i}}" >> /etc/resolv.conf;
              {% endfor -%}{% endif%}
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
    - watch:
      - mc_proxy: ms-dns-pre-{{suf}}
      {% if watch %}
      {% for w in watch %}
      - {{w}}
      {% endfor %}
      {% endif %}
    - watch_in:
      - mc_proxy: ms-dns-post-{{suf}}
      {% if watch_in %}
      {% for w in watch_in %}
      - {{w}}
      {% endfor %}
      {% endif %}

{% if grains['os'] in ['Ubuntu'] %}
bind-set-defaultdns-{{suf}}-2:
  cmd.run:
    - name: /bin/true
    - unless: |
            #!/usr/bin/env bash
            rm /etc/resolvconf/resolv.conf.d/head;
            echo > /etc/resolvconf/resolv.conf.d/head;
            echo '# nameservers setted by makina-states'> /etc/resolvconf/resolv.conf.d/head;
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
    - watch:
      - mc_proxy: ms-dns-pre-{{suf}}
      {% if watch %}
      {% for w in watch %}
      - {{w}}
      {% endfor %}
      {% endif %}
    - watch_in:
      - mc_proxy: ms-dns-post-{{suf}}
      {% if watch_in %}
      {% for w in watch_in %}
      - {{w}}
      {% endfor %}
      {% endif %}
{% endif %}

{% endif %}
{% endmacro %}
