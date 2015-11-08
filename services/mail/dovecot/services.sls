include:
  - makina-states.services.mail.dovecot.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
makina-dovecot-service:
  service.running:
    - name: dovecot
    - enable: True
    - watch:
      - mc_proxy: dovecot-pre-restart-hook
    - watch_in:
      - mc_proxy: dovecot-post-restart-hook
{% endif %}
