{#- Postfix SMTP Server managment #}
include:
  - makina-states.services.mail.postfix.hooks
postfix-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - postfix
      - postfix-pcre
    - watch:
      - mc_proxy: postfix-pre-install-hook
    - watch_in:
      - mc_proxy: postfix-post-install-hook
