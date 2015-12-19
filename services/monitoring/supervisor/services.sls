include:
  - makina-states.services.monitoring.supervisor.hooks
{% if salt['mc_nodetypes.activate_sysadmin_states']() %}
{% if not salt['mc_nodetypes.is_docker']() %}
{% set settings = salt['mc_supervisor.settings']() %}
supervisor-hard-start:
  service.running:
    - names: {{settings.services}}
    - enable: True
    - watch:
      - mc_proxy: supervisor-pre-hard-restart
    - watch_in:
      - mc_proxy: supervisor-post-hard-restart
supervisor-start:
  service.running:
    - names: {{settings.services}}
    - enable: True
    - reload: True
    - watch:
      - mc_proxy: supervisor-pre-restart
    - watch_in:
      - mc_proxy: supervisor-post-restart
{% endif %}
{% endif %}
