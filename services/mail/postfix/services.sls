include:
  - makina-states.services.mail.postfix.hooks
{% set locs = salt['mc_locations.settings']()%}

makina-postfix-configuration-check:
  cmd.run:
    - name: {{ locs.sbin_dir }}/postfix check 2>&1  && echo "" && echo "changed=no"
    - stateful: True
    - watch:
      - mc_proxy: postfix-post-conf-hook
    - watch_in:
      - mc_proxy: postfix-pre-restart-hook

makina-postfix-service:
  service.running:
    - name: postfix
    - enable: True
    - watch_in:
      - mc_proxy: postfix-post-restart-hook
    - watch:
      - mc_proxy: postfix-pre-restart-hook
