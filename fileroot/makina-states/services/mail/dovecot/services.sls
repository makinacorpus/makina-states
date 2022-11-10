include:
  - makina-states.services.mail.dovecot.hooks
makina-dovecot-service:
  service.running:
    - name: dovecot
    - enable: True
    - watch:
      - mc_proxy: dovecot-pre-restart-hook
    - watch_in:
      - mc_proxy: dovecot-post-restart-hook
