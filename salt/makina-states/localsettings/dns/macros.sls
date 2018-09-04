{% set settings = salt['mc_dns.settings']() %}
{% macro switch_dns(suf,
                    search=None,
                    dnsservers=None,
                    require=None,
                    require_in=None,
                    watch=None,
                    watch_in=None) %}
{% if not dnsservers %}{% set dnsservers = settings.default_dnses %}{%endif%}
{% if not search %}{% set search = settings.search %}{%endif%}
{% if not require %}{% set require = [] %}{% endif %}
{% if not require_in %}{% set require_in = [] %}{% endif %}
{% if not require %}{% set watch = [] %}{% endif %}
{% if not watch_in %}{% set watch_in = [] %}{% endif %}
{% if search %}
{%  set search = ' '.join(salt['mc_utils.uniquify'](search)) %}
{% else %}
{%  set search = '' %}
{% endif %}
{% if dnsservers %}
{%  set dnsservers = ' '.join(salt['mc_utils.uniquify'](dnsservers)) %}
{% else %}
{%  set dnsservers = '' %}
{%endif %}

{# hooks for dns orchestration #}
ms-dns-pre-{{suf}}:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: ms-dns-post-{{suf}}

ms-dns-post-{{suf}}:
  mc_proxy.hook: []
bind-set-defaultdns-{{suf}}-1:
  file.managed:
    - name: /usr/bin/ms-resolv-conf.sh
    - source: salt://makina-states/files/usr/bin/ms-resolv-conf.sh
    - user: root
    - group: root
    - mode: 755
  cmd.run:
    - user: root
    {# only if dnsmasq/resolvconf is there #}
    - name: /bin/true
    {% if (dnsservers or search) %}
    - unless: /usr/bin/ms-resolv-conf.sh
    {% else %}
    - unless: /bin/true
    {% endif %}
    - env:
        DNS_SERVERS: "{{dnsservers}}"
        DNS_SEARCH: "{{search}}"
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
      - file: bind-set-defaultdns-{{suf}}-1
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

{# left for retrocompat #}
bind-set-defaultdns-{{suf}}-2:
  cmd.run:
    - name: /bin/true
    - onlyif: /bin/false
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
{% endmacro %}
