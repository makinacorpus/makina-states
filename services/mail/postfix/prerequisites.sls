{#- Postfix SMTP Server managment #}
include:
  - makina-states.services.mail.postfix.hooks
{% if salt['mc_controllers.mastersalt_mode']() %}
postfix-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - postfix
      - postfix-pcre
      - procmail
    - watch:
      - mc_proxy: postfix-preinstall
    - watch_in:
      - mc_proxy: postfix-postinstall
{%endif %}
