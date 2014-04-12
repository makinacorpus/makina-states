include:
  - makina-states.services.mail.dovecot.hooks
dovecot-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - dovecot-common
      - dovecot-imapd
