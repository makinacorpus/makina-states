{#-
# Dovecot POP/IMAP Server managment
#
# ------------------------- START pillar example -----------
# --- DOVECOT -----------------------------
#
# do not forget to launch "salt '*' saltutil.refresh_pillar" after changes
# consult pillar values with "salt '*' pillar.items"
# --------------------------- END pillar example ------------
#}
{% set locs = salt['mc_locations.settings']() %}
#--- DEV SERVER: ALL EMAILS ARE IN A LOCAL vagrant MAILBOX
include:
  - makina-states.services.mail.dovecot.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% if salt['mc_nodetypes.is_devhost']() %}
makina-dovecot-dev-imap-conf:
  file.managed:
    - name: {{ locs.conf_dir }}/dovecot/local.conf
    - source: salt://makina-states/files/etc/dovecot/local.conf.imap.dev.server
    - watch_in:
      - mc_proxy: dovecot-post-conf-hook
    - watch:
      - mc_proxy: dovecot-pre-conf-hook
    - template: jinja
    - user: root
    - group: dovecot
    - mode: 644
    - defaults:
      mailname: {{ grains['fqdn'] }}
      spool: {{ locs.var_spool_dir }}
{% endif %}
{% endif %}
# ------------ dev mode end -----------------------
