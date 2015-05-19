include:
  - makina-states.localsettings.ssl.hooks
{# postfix orchestration hooks #}
postfix-preinstall:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: postfix-postinstall
      - mc_proxy: postfix-preconf
      - mc_proxy: postfix-postconf
      - mc_proxy: postfix-prerestart
      - mc_proxy: postfix-postrestart

postfix-postinstall:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: postfix-preconf
      - mc_proxy: postfix-postconf
      - mc_proxy: postfix-prerestart
      - mc_proxy: postfix-postrestart

postfix-preconf:
  mc_proxy.hook:
    - watch:
      - mc_proxy: ssl-certs-post-hook
    - watch_in:
      - mc_proxy: postfix-postconf
      - mc_proxy: postfix-prerestart
      - mc_proxy: postfix-postrestart

postfix-postconf:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: postfix-prerestart
      - mc_proxy: postfix-postrestart

postfix-prerestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: postfix-postrestart

postfix-postrestart:
  mc_proxy.hook: []


postfix-prehardrestart:
  mc_proxy.hook:
    - watch_in:
      - mc_proxy: postfix-posthardrestart

postfix-posthardrestart:
  mc_proxy.hook: []

