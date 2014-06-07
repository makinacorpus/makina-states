include:
  - makina-states.services.firewall.psad.hooks
psad-service:
  service.running:
    - name: psad
    - enable: True
    - watch:
      - mc_proxy: psad-pre-restart-hook
    - watch_in:
      - mc_proxy: psad-post-restart-hook
