{% set data = salt['mc_burp.settings']() %}
include:
  - makina-states.services.backup.burp.hooks
#
# cleanup the configuration directories from stale clients configuration
# data cleanup as it is backups is left to manually done by
# sysadmins. Cleaning automatically old backups can be cumbersome
# and dangerous
#
install-burp-configuration-cleanup:
  file.managed:
    - source: salt://makina-states/files/etc/burp/cleanup.sh
    - name: /etc/burp/cleanup.sh
    - mode: 0755
    - user: root
    - template: jinja
    - group: root
  cmd.run:
    - name: /etc/burp/cleanup.sh
    - use_vt: true
    - watch:
      - mc_proxy: burp-post-restart-hook
