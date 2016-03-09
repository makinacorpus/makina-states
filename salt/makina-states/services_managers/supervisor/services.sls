include:
  - makina-states.services_managers.supervisor.hooks
{%  set settings = salt['mc_supervisor.settings']() %}
{%  if salt['mc_nodetypes.has_system_services_manager']() %}
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
{%  endif %}
