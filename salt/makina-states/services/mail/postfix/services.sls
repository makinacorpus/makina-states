include:
  - makina-states.services.mail.postfix.hooks
{% set locs = salt['mc_locations.settings']()%}

makina-postfix-configuration-check:
  cmd.run:
    - name: {{ locs.sbin_dir }}/postfix check 2>&1  && echo "" && echo "changed=no"
    - stateful: True
    - watch:
      - mc_proxy: postfix-postconf
    - watch_in:
      - mc_proxy: postfix-prerestart

makina-postfix-service:
  service.running:
    - name: postfix
    - enable: True
    - watch_in:
      - mc_proxy: postfix-postrestart
    - watch:
      - mc_proxy: postfix-prerestart


makina-postfix-cli-client:
  pkg.latest:
    - pkgs: [mailutils]
    - watch_in:
      - service: makina-postfix-service
      - mc_proxy: postfix-postrestart
    - watch:
      - mc_proxy: postfix-prerestart 
