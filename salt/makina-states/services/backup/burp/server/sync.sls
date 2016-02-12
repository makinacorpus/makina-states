{% set data = salt['mc_burp.settings']() %}
include:
  - makina-states.services.backup.burp.hooks
install-burp-configuration-sync:
  file.managed:
    - source: salt://makina-states/files/etc/burp/clients/sync.py
    - name: /etc/burp/clients/sync.py
    - mode: 0755
    - template: jinja
    - user: root
    - group: root
  cmd.run:
    - name: /etc/burp/clients/sync.py
    - use_vt: true
    - watch:
      - file: install-burp-configuration-sync
      - mc_proxy: burp-post-gen-sync
    - watch_in:
      - mc_proxy: burp-post-sync
