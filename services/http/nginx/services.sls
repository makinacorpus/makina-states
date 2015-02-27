include:
  - makina-states.services.http.nginx.hooks
#--- MAIN SERVICE RESTART/RELOAD requireers --------------
# Configuration checker, always run before restart of graceful restart
{% set settings = salt['mc_nginx.settings']() %}
makina-nginx-conf-syntax-check:
  cmd.run:
    - name: {{ salt['mc_salt.settings']().msr }}/_scripts/nginxConfCheck.sh
    - stateful: True
    - watch:
      - mc_proxy: nginx-pre-restart-hook
      - mc_proxy: nginx-pre-hardrestart-hook
    - watch_in:
      - service: makina-nginx-restart
      - service: makina-nginx-reload

{# compat: reload #}
{% for i in ['reload', 'restart'] %}
makina-nginx-{{i}}:
  service.running:
    - name: {{ settings.service }}
    - enable: True
    - watch_in:
      - mc_proxy: nginx-post-restart-hook
      - mc_proxy: nginx-post-hardrestart-hook
    - watch:
      - mc_proxy: nginx-pre-restart-hook
      - mc_proxy: nginx-pre-hardrestart-hook
{% endfor %}

makina-ngin-naxsi-ui-running:
{# totally disable naxui for now #}
{% if False %}
  service.running:
    - enable: True
{% else %}
  service.dead:
    - enable: False
{% endif %}
    - name: nginx-naxsi-ui
    - require_in:
      - mc_proxy: nginx-post-restart-hook
    - require:
      - mc_proxy: nginx-pre-restart-hook
