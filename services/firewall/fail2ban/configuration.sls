{%- set data = salt['mc_fail2ban.settings']() %}
include:
  - makina-states.services.firewall.fail2ban.hooks
  - makina-states.services.firewall.fail2ban.services
{%- set locs = salt['mc_locations.settings']()%}
{% if salt['mc_controllers.mastersalt_mode']() %}
makina-fail2ban-pre-conf:
  mc_proxy.hook: []

{% for f in ['fail2ban/jail.conf',
             'init.d/fail2ban'] %}
makina-etc-{{f}}:
  file.managed:
    - name: {{ locs.conf_dir }}/{{f}}
    - source : salt://makina-states/files/etc/{{f}}
    - template: jinja
    - user: root
    - group: root
    - mode: "0700"
    - watch:
      - mc_proxy: fail2ban-pre-conf-hook
    - watch_in:
      - mc_proxy: fail2ban-post-conf-hook
{% endfor %}

makina-etc-fail2ban-fail2ban-conf:
  file.managed:
    - name: {{ locs.conf_dir }}/fail2ban/fail2ban.conf
    - source : salt://makina-states/files/etc/fail2ban/fail2ban.conf
    - template: jinja
    - user: root
    - group: root
    - mode: "0700"
    - watch:
      - mc_proxy: makina-fail2ban-pre-conf
    - watch_in:
      - mc_proxy: fail2ban-post-conf-hook
{% endif %}

{% for i in data.get('filters', {}) %}
makina-etc-filter{{i}}:
  file.managed:
    - name: /etc/fail2ban/filter.d/{{i}}.conf
    - source : salt://makina-states/files/etc/fail2ban/filter.d/autofilter.conf
    - template: jinja
    - user: root
    - group: root
    - mode: "0700"
    - defaults:
        name: "{{i}}"
    - watch:
      - mc_proxy: fail2ban-pre-conf-hook
    - watch_in:
      - mc_proxy: fail2ban-post-conf-hook
{% endfor %}

{% for i in data.get('jails', {}) %}
makina-etc-jail{{i}}:
  file.managed:
    - name: /etc/fail2ban/jail.d/{{i}}.conf
    - source : salt://makina-states/files/etc/fail2ban/jail.d/autojail.conf
    - template: jinja
    - user: root
    - defaults:
        name: "{{i}}"
    - group: root
    - mode: "0700"
    - watch:
      - mc_proxy: fail2ban-pre-conf-hook
    - watch_in:
      - mc_proxy: fail2ban-post-conf-hook
{% endfor %}
