{% set data = salt['mc_burp.settings']() %}
include:
  - makina-states.services.backup.burp.hooks
  - makina-states.services.backup.burp.server.sync
  - makina-states.services.backup.burp.server.cleanup
burp-svc:
  service.running:
    - name:  burp-server
    - reload: True
    - watch:
      - mc_proxy: burp-pre-restart-hook
    - watch_in:
      - mc_proxy: burp-post-restart-hook
