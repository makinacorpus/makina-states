include:
  - makina-states.services_managers.circus.hooks

{% if salt['mc_controllers.allow_lowlevel_states']() %}
  - makina-states.services_managers.circus.unregister

{%  set settings = salt['mc_circus.settings']() %}

{%  if salt['mc_nodetypes.has_system_services_manager']() %}
circus-stop-circus:
  service.dead:
    - names: {{settings.services}}
    - watch:
      - mc_proxy: circus-pre-disable
    - watch_in:
      - file: circus-disable-makinastates-circus
      - mc_proxy: circus-post-disable
{%  endif %}

circus-disable-makinastates-circus:
  file.absent:
    - names:
      - {{settings.venv}}
      - /etc/circus.d
      - /etc/init/circusd.conf
      - /etc/circus
      - /etc/logrotate.d/circus.conf
      - /var/log/circusd.log
      - /var/log/circus
      {% for i in settings.configs %}- {{i}}
      {%endfor%}
    - watch:
      - mc_proxy: circus-pre-disable
    - watch_in:
      - mc_proxy: circus-post-disable
{% endif %}
