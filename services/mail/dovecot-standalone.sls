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
{% macro do(full=True) %}
{{ salt['mc_macros.register']('services', 'mail.dovecot') }}
{% set locs = salt['mc_localsettings.settings']()['locations'] %}
{% if full %}
dovecot-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - dovecot-common
      - dovecot-imapd
{% endif %}

#--- DEV SERVER: ALL EMAILS ARE IN A LOCAL vagrant MAILBOX
{% if salt['mc_nodetypes.registry]()['is']['devhost'] %}
makina-dovecot-dev-imap-conf:
  file.managed:
    - name: {{ locs.conf_dir }}/dovecot/local.conf
    - source: salt://makina-states/files/etc/dovecot/local.conf.imap.dev.server
    {% if full %}
    - require:
      - pkg: dovecot-pkgs
    {% endif %}
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
    {% if full %}
    - require:
      - pkg: dovecot-pkgs
      #- cmd: makina-dovecot-configuration-check
    - watch:
      # restart service in case of package install
      - pkg: dovecot-pkgs
    {% endif %}
{% endmacro %}
{{ do(full=False) }}
