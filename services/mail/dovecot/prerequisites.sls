include:
  - makina-states.services.mail.dovecot.hooks
dovecot-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - dovecot-common
      - dovecot-imapd
