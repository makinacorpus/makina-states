include:
  - makina-states.services_managers.circus.hooks
{%  set settings = salt['mc_circus.settings']() %}
{%  if salt['mc_nodetypes.has_system_services_manager']() %}
circus-hard-start:
  service.running:
    - names: {{settings.services}}
    - enable: True
    - watch:
      - mc_proxy: circus-pre-hard-restart
    - watch_in:
      - mc_proxy: circus-post-hard-restart
circus-start:
  service.running:
    - names: {{settings.services}}
    - enable: True
    - reload: True
    - watch:
      - mc_proxy: circus-pre-restart
    - watch_in:
      - mc_proxy: circus-post-restart
{%  endif %}
