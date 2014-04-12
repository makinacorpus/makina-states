include:
  - makina-states.services.mail.postfix.hooks
makina-postfix-service:
  service.running:
    - name: postfix
    - enable: True
    - watch_in:
      - mc_proxy: postfix-post-restart-hook
    - watch:
      - mc_proxy: postfix-pre-restart-hook
