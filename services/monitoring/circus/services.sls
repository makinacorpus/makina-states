include:
  - makina-states.services.monitoring.circus.hooks
{% if salt['mc_nodetypes.activate_sysadmin_states']() %}
{% if not salt['mc_nodetypes.is_docker']() %}
{% set settings = salt['mc_circus.settings']() %}
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
{% endif %}
{% endif %}
