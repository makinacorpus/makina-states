{#-
# Postfix SMTP Server managment
#
# ------------------------- START pillar example -----------
# --- POSTFIX -----------------------------
#
# do not forget to launch "salt '*' saltutil.refresh_pillar" after changes
# consult pillar values with "salt '*' pillar.items"
# --------------------------- END pillar example ------------
#
#}
{% macro do(full=True) %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{{ salt['mc_macros.register']('services', 'mail.postfix') }}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set locs = localsettings.locations %}
{% if full %}
postfix-pkgs:
  pkg.installed:
    - pkgs:
      - postfix
      - postfix-pcre
{% endif %}

#--- DEV SERVER: CATCH ALL EMAILS TO A LOCAL MAILBOX
{% if nodetypes.registry.is.devhost and not nodetypes.registry.is.travis %}
  {% set ips=grains['ip_interfaces'] %}
  {% set ip1=ips['eth0'][0] %}
  {% set ip2=ips['eth1'][0] %}
  {% set ipd=ips['docker0'][0] %}
  {% set netip1='.'.join(ip1.split('.')[:3])+'.0/24' %}
  {% set netip2='.'.join(ip2.split('.')[:3])+'.0/24' %}
  {% set netipd='.'.join(ipd.split('.')[:3])+'.0/24' %}
  {% set local_networks = netip1 + ' ' + netip2 + ' ' + netipd %}

{{ locs.conf_dir }}-postfix-main.cf:
  file.managed:
    - name: {{ locs.conf_dir }}/postfix/main.cf
    - source: salt://makina-states/files/etc/postfix/main.cf.localdeliveryonly
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    {% if full%}
    - require:
      - pkg: postfix-pkgs
    {% endif %}
    - require_in:
      - cmd: makina-postfix-configuration-check
    - watch_in:
      # restart service in case of settings alterations
      - service: makina-postfix-service
    - defaults:
        conf_dir: {{ locs.conf_dir }}
        mailname: {{ grains['fqdn'] }}
        local_networks: {{ local_networks }}

makina-postfix-local-catch-all-delivery-virtual:
  file.managed:
    - name: {{ locs.conf_dir }}/postfix/virtual
    - source: salt://makina-states/files/etc/postfix/virtual.localdeliveryonly
    - user: root
    - group: root
    - mode: 644
    {% if full %}
    - require:
      - pkg: postfix-pkgs
    {% endif %}
    - require_in:
      - cmd: makina-postfix-configuration-check

makina-postfix-aliases-all-to-vagrant-user:
  file.append:
    - name: {{ locs.conf_dir }}/aliases
    {% if full %}
    - require:
      - pkg: postfix-pkgs
    {% endif %}
    - text:
      - "root: vagrant"
    - require_in:
      - cmd: makina-postfix-configuration-check

# postmap /etc/postfix/virtual when altered
makina-postfix-postmap-virtual-dev:
  cmd.watch:
    - name: postmap {{ locs.conf_dir }}/postfix/virtual;echo "changed=yes"
    - stateful: True
    {% if full %}
    - require:
      - pkg: postfix-pkgs
    {% endif %}
    - watch:
      - file: makina-postfix-local-catch-all-delivery-virtual
    - require_in:
      - service: makina-postfix-service

# postalias if {{ locs.conf_dir }}/aliases is altered
makina-postfix-postalias-dev:
  cmd.watch:
    - stateful: True
    - name: postalias {{ locs.conf_dir }}/aliases;echo "changed=yes"
    - watch:
      - file: makina-postfix-aliases-all-to-vagrant-user
    - require_in:
      - service: makina-postfix-service

# ------------ dev mode end -----------------------
{% endif %}


makina-postfix-chroot-hosts-sync:
  cmd.run:
    - unless: diff -q {{ locs.var_spool_dir }}/postfix/etc/hosts {{ locs.conf_dir }}/hosts
    - stateful: True
    - name: cp -a {{ locs.conf_dir }}/hosts {{ locs.var_spool_dir }}/postfix/etc/hosts && echo "" && echo "changed=yes"
    {% if full %}
    - require:
      - pkg: postfix-pkgs
    {% endif %}

makina-postfix-chroot-localtime-sync:
  cmd.run:
    - unless: diff -q {{ locs.var_spool_dir }}/postfix/etc/localtime {{ locs.conf_dir }}/localtime
    - stateful: True
    - name: cp -a {{ locs.conf_dir }}/localtime {{ locs.var_spool_dir }}/postfix/etc/localtime && echo "" && echo "changed=yes"
    {% if full %}
    - require:
      - pkg: postfix-pkgs
    {% endif %}

makina-postfix-chroot-nsswitch-sync:
  cmd.run:
    - unless: diff -q {{ locs.var_spool_dir }}/postfix/etc/nsswitch.conf {{ locs.conf_dir }}/nsswitch.conf
    - stateful: True
    - name: cp -a {{ locs.conf_dir }}/nsswitch.conf  {{ locs.var_spool_dir }}/postfix/etc/nsswitch.conf  && echo "" && echo "changed=yes"
    {% if full %}
    - require:
      - pkg: postfix-pkgs
    {% endif %}
makina-postfix-chroot-resolvconf-sync:
  cmd.run:
    - unless: diff -q {{ locs.var_spool_dir }}/postfix/etc/resolv.conf {{ locs.conf_dir }}/resolv.conf
    - stateful: True
    - name: cp -a {{ locs.conf_dir }}/resolv.conf {{ locs.var_spool_dir }}/postfix/etc/resolv.conf && echo "" && echo "changed=yes"
    {% if full %}
    - require:
      - pkg: postfix-pkgs
    {% endif %}

makina-postfix-configuration-check:
  cmd.run:
    - name: {{ locs.sbin_dir }}/postfix check 2>&1  && echo "" && echo "changed=no"
    - stateful: True
    - require:
      {%  if full %}
      - pkg: postfix-pkgs
      {% endif %}
      - cmd: makina-postfix-chroot-hosts-sync
      - cmd: makina-postfix-chroot-resolvconf-sync
      - cmd: makina-postfix-chroot-nsswitch-sync
      - cmd: makina-postfix-chroot-localtime-sync

#--- MAIN SERVICE RESTART/RELOAD watchers
makina-postfix-service:
  service.running:
    - name: postfix
    - enable: True
    - require:
      {% if full %}
      - pkg: postfix-pkgs
      {% endif %}
      - cmd: makina-postfix-configuration-check
    - watch:
      # restart service in case of package install
      {% if full %}
      - pkg: postfix-pkgs
      {% endif %}
      # restart service if {{ locs.conf_dir }}/hosts were altered?
      - cmd: makina-postfix-chroot-hosts-sync
{% endmacro %}
{{ do(full=False) }}
