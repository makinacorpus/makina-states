# Dovecot POP/IMAP Server managment
#
# ------------------------- START pillar example -----------
# --- DOVECOT -----------------------------
#
# do not forget to launch "salt '*' saltutil.refresh_pillar" after changes
# consult pillar values with "salt '*' pillar.items"
# --------------------------- END pillar example ------------
#
{% import "makina-states/_macros/services.jinja" as services with context %}
{{ salt['mc_macros.register']('services', 'mail.dovecot') }}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set locs = localsettings.locations %}
dovecot-pkgs:
  pkg.installed:
    - pkgs:
      - dovecot-common
      - dovecot-imapd

#--- DEV SERVER: ALL EMAILS ARE IN A LOCAL vagrant MAILBOX
{% if 'devhost' in nodetypes.registry['actives'] %}
makina-dovecot-dev-imap-conf:
  file.managed:
    - name: {{ locs.conf_dir }}/dovecot/local.conf
    - source: salt://makina-states/files/etc/dovecot/local.conf.imap.dev.server
    - require:
      - pkg: dovecot-pkgs
    - watch_in:
      # restart service in case of settings alterations
      - service: makina-dovecot-service
    - template: jinja
    - user: root
    - group: dovecot
    - mode: 644
    - defaults:
      mailname: {{ grains['fqdn'] }}
      spool: {{ locs.var_spool_dir }}

# ------------ dev mode end -----------------------
{% endif %}

#--- MAIN SERVICE RESTART/RELOAD watchers
makina-dovecot-service:
  service.running:
    - name: dovecot
    - enable: True
    - require:
      - pkg: dovecot-pkgs
      #- cmd: makina-dovecot-configuration-check
    - watch:
      # restart service in case of package install
      - pkg: dovecot-pkgs
