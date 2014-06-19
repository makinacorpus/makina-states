include:
  - makina-states.services.firewall.fail2ban.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
fail2ban-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - fail2ban
    - watch:
      - mc_proxy: fail2ban-pre-install-hook
    - watch_in:
      - mc_proxy: fail2ban-post-install-hook
{% endif %}

