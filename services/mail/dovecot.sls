# Dovecot POP/IMAP Server managment
#
# ------------------------- START pillar example -----------
# --- DOVECOT -----------------------------
#
# do not forget to launch "salt '*' saltutil.refresh_pillar" after changes 
# consult pillar values with "salt '*' pillar.items"
# --------------------------- END pillar example ------------
#

dovecot-pkgs:
  pkg.installed:
    - names:
      - dovecot-common
      - dovecot-imapd

#--- DEV SERVER: ALL EMAILS ARE IN A LOCAL vagrant MAILBOX
{% if grains['makina.devhost'] %}
makina-dovecot-dev-imap-conf:
  file.managed:
    - name: /etc/dovecot/local.conf
    - source: salt://makina-states/files/etc/dovecot/local.conf.imap.dev.server
    - require:
      - pkg.installed: dovecot-pkgs
    - template: jinja
    - user: root
    - group: dovecot
    - mode: 644
    - defaults:
      mailname: {{ grains['fqdn'] }}

# ------------ dev mode end -----------------------
{% endif %}



#--- MAIN SERVICE RESTART/RELOAD watchers

makina-dovecot-service:
  service.running:
    - name: dovecot
    - enable: True
    - require:
      - pkg.installed: dovecot-pkgs
      #- cmd: makina-dovecot-configuration-check
    - watch:
      # restart service in case of package install
      - pkg.installed: dovecot-pkgs
      # restart service in case of settings alterations
{% if grains['makina.devhost'] %}
      - file: makina-dovecot-dev-imap-conf
{% endif %}

