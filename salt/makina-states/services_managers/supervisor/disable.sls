include:
  - makina-states.services_managers.supervisor.hooks
  - makina-states.services_managers.supervisor.unregister

{%  set settings = salt['mc_supervisor.settings']() %}

{%  if salt['mc_nodetypes.has_system_services_manager']() %}
supervisor-stop-supervisor:
  service.dead:
    - names: {{settings.services}}
    - watch:
      - mc_proxy: supervisor-pre-disable
    - watch_in:
      - file: supervisor-disable-makinastates-supervisor
      - mc_proxy: supervisor-post-disable
{%  endif %}

supervisor-disable-makinastates-supervisor:
  file.absent:
    - names:
      - {{settings.venv}}
      - /etc/supervisor.d
      - /etc/logrotate.d/supervisor.conf
      - /etc/init/ms_supervisor.conf
      - /etc/supervisor
      - /var/log/supervisord.log
      - /var/log/supervisor
      {% for i in settings.configs %}- {{i}}
      {%endfor%}
    - watch:
      - mc_proxy: supervisor-pre-disable
    - watch_in:
      - mc_proxy: supervisor-post-disable
