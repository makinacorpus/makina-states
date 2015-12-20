{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% set settings = salt['mc_circus.settings']() %}
include:
  - makina-states.services.monitoring.circus.hooks
  - makina-states.services.monitoring.circus.unregister
{% if not salt['mc_nodetypes.is_docker'] %}
circus-stop-circus:
  service.dead:
    - names: [circusd]
    - watch:
      - mc_proxy: circus-pre-disable
    - watch_in:
      - mc_proxy: circus-post-disable
{% endif %}
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
      - service: circus-stop-circus
      - mc_proxy: circus-pre-disable
    - watch_in:
      - mc_proxy: circus-post-disable
{%endif %}
