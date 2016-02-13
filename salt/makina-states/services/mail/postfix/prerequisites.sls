{#- Postfix SMTP Server managment #}
include:
  - makina-states.services.mail.postfix.hooks
  {% if salt['mc_controllers.allow_lowlevel_states']() %}
postfix-preseed_nointeractive:
  debconf.set:
    - name: postfix
    - data:
        "postfix/main_mailer_type": {'type': "select", 'value': "No configuration"}
        "postfix/mailname": {'type': "string", 'value': "localhost"}
        "postfix/destinations": {'type': "string",
                                 'value': "localhost.localdomain, localhost"}

    - watch:
      - mc_proxy: postfix-preinstall
    - watch_in:
      - mc_proxy: postfix-postinstall
postfix-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - postfix
      - postfix-pcre
      - procmail
    - watch:
      - debconf: postfix-preseed_nointeractive
      - mc_proxy: postfix-preinstall
    - watch_in:
      - mc_proxy: postfix-postinstall
{%endif %}
