{% set data = salt['mc_ntp.settings']() %}
include:
  - makina-states.services.base.ntp.hooks
{% if not salt['mc_nodetypes.is_docker']() %}
{%- if grains['os'] not in ['Debian', 'Ubuntu'] %}
ntpdate-svc:
  service.enabled:
    - watch_in:
      - mc_proxy: ntp-post-restart-hook
    - watch:
      - mc_proxy: ntp-pre-restart-hook
    - name: ntpdate
{%- endif %}

ntpd:
{% if data['activated'] %}
  service.running:
    - enable: True
{% else %}
  service.dead:
    - enable: false
{%- endif %}
    - watch_in:
      - mc_proxy: ntp-post-restart-hook
    - watch:
      - mc_proxy: ntp-pre-restart-hook
    {%- if grains['os'] in ['Debian', 'Ubuntu'] %}
    - name: ntp
    {%- endif %}
{%- endif %}

{% if data['activated'] %}
ntpd-sync:
  cmd.run:
    - name: /sbin/ntp-sync.sh
    - stateful: true
    - watch_in:
      - mc_proxy: ntp-post-restart-hook
    - watch:
      - service: ntpd
      - mc_proxy: ntp-pre-restart-hook
{%else%}
ntpd-kill:
  cmd.run:
    - name: /sbin/ntp-kill.sh
    - stateful: true
    - watch_in:
      - mc_proxy: ntp-post-restart-hook
    - watch:
      - service: ntpd
      - mc_proxy: ntp-pre-restart-hook
{%- endif %}
