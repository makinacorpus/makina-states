include:
  - makina-states.services.firewall.fail2ban.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
fail2ban-service:
  service.running:
    - name: fail2ban
    - enable: True
    - watch:
      - mc_proxy: fail2ban-pre-hardrestart-hook
    - watch_in:
      - mc_proxy: fail2ban-post-hardrestart-hook

{% endif %}
