{%- set data = salt['mc_fail2ban.settings']() %}
include:
  - makina-states.services.firewall.fail2ban.hooks
  - makina-states.services.firewall.fail2ban.services
{%- set locs = salt['mc_locations.settings']()%}
{% if salt['mc_controllers.mastersalt_mode']() %}
makina-fail2ban-pre-conf:
  mc_proxy.hook: []
makina-etc-fail2ban-fail-conf:
  file.managed:
    - name: {{ locs.conf_dir }}/fail2ban/jail.conf
    - source : salt://makina-states/files/etc/fail2ban/jail.conf
    - template: jinja
    - user: root
    - group: root
    - mode: "0700"
    - defaults:
      data: |
            {{salt['mc_utils.json_dump']( data)}}
    - watch:
      - mc_proxy: fail2ban-pre-conf-hook
    - watch_in:
      - mc_proxy: fail2ban-post-conf-hook

makina-etc-fail2ban-fail2ban-conf:
  file.managed:
    - name: {{ locs.conf_dir }}/fail2ban/fail2ban.conf
    - source : salt://makina-states/files/etc/fail2ban/fail2ban.conf
    - template: jinja
    - user: root
    - group: root
    - mode: "0700"
    - defaults:
      data: |
            {{salt['mc_utils.json_dump']( data)}}
    - watch:
      - mc_proxy: makina-fail2ban-pre-conf
    - watch_in:
      - mc_proxy: fail2ban-post-conf-hook
{% endif %}
