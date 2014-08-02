{% set data = salt['mc_mumble.settings']() %}
{%set sdata = salt['mc_utils.json_dump'](data) %}
include:
  - makina-states.services.sound.mumble.hooks

makina-mumble-service:
  service.running:
    - names:
      - mumble-server
    - enable: true
    - watch:
      - mc_proxy: mumble-pre-restart-hook
    - watch_in:
      - mc_proxy: mumble-post-restart-hook

makina-mumble-password:
  cmd.run:
    - name: murmurd -supw {{data.murmur.supassword}}
    - user: root
    - watch:
      - mc_proxy: mumble-post-restart-hook
