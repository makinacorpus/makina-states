include:
  - makina-states.services.base.ntp.hooks
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
  service.running:
    - watch_in:
      - mc_proxy: ntp-post-restart-hook
    - watch:
      - mc_proxy: ntp-pre-restart-hook
    - enable: True
    {%- if grains['os'] in ['Debian', 'Ubuntu'] %}
    - name: ntp
    {%- endif %}
