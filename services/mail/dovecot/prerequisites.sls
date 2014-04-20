include:
  - makina-states.services.mail.dovecot.hooks
dovecot-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - dovecot-common
      - dovecot-imapd
    - watch:
      - mc_proxy: dovecot-pre-install-hook
    - watch_in:
      - mc_proxy: dovecot-post-install-hook
