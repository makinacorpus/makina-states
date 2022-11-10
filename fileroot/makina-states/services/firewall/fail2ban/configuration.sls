{% import "makina-states/_macros/h.jinja" as h with context %}
{%- set data = salt['mc_fail2ban.settings']() %}
include:
  - makina-states.services.firewall.fail2ban.hooks
  - makina-states.services.firewall.fail2ban.services
{%- set locs = salt['mc_locations.settings']()%}
makina-fail2ban-pre-conf:
  mc_proxy.hook: []
{% macro rmacro() %}
    - watch:
      - mc_proxy: fail2ban-pre-conf-hook
    - watch_in:
      - mc_proxy: fail2ban-post-conf-hook
{% endmacro %}
{{ h.deliver_config_files(
     data.get('extra_confs', {}), after_macro=rmacro, prefix='fwld-')}}
{% for j in ['filter', 'jail', 'action'] %}
{% for i in data.get('{0}s'.format(j), {}) %}
makina-etc-{{j}}-{{i}}:
  file.managed:
    - name: "/etc/fail2ban/{{j}}.d/{{i}}.conf"
    - source : "salt://makina-states/files/etc/fail2ban/{{j}}.d/auto{{j}}.conf"
    - template: jinja
    - user: root
    - group: root
    - makedirs: true
    - mode: "0700"
    - defaults:
        name: "{{i}}"
    - watch:
      - mc_proxy: fail2ban-pre-conf-hook
    - watch_in:
      - mc_proxy: fail2ban-post-conf-hook
{% endfor %}
{% endfor %}
