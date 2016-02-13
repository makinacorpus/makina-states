include:
  - makina-states.services.mail.dovecot.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
dovecot-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      {% if grains.get('lsb_distrib_codename', grains.get('oscodename', 'foo')) in ['lucid'] %}
      - dovecot-common
      {% else %}
      {# salt is not easy with virtual packages ... #}
      - dovecot-core
      {% endif%}
      - dovecot-imapd
    - watch:
      - mc_proxy: dovecot-pre-install-hook
    - watch_in:
      - mc_proxy: dovecot-post-install-hook
{% endif %}
