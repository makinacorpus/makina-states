# Postfix SMTP Server managment
#
# ------------------------- START pillar example -----------
# --- POSTFIX -----------------------------
#
# do not forget to launch "salt '*' saltutil.refresh_pillar" after changes 
# consult pillar values with "salt '*' pillar.items"
# --------------------------- END pillar example ------------
#

postfix-pkgs:
  pkg.installed:
    - names:
      - postfix
      - postfix-pcre

#--- DEV SERVER: CATCH ALL EMAILS TO A LOCAL MAILBOX
{% if grains['makina.nodetype.devhost'] %}

  {% set ips=grains['ip_interfaces'] %}
  {% set ip1=ips['eth0'][0] %}
  {% set ip2=ips['eth1'][0] %}
  {% set ipd=ips['docker0'][0] %}
  {% set netip1='.'.join(ip1.split('.')[:3])+'.0/24' %}
  {% set netip2='.'.join(ip2.split('.')[:3])+'.0/24' %}
  {% set netipd='.'.join(ipd.split('.')[:3])+'.0/24' %}
  {% set local_networks = netip1 + ' ' + netip2 + ' ' + netipd %}

makina-postfix-local-catch-all-delivery-conf:
  file.managed:
    - name: /etc/postfix/main.cf
    - source: salt://makina-states/files/etc/postfix/main.cf.localdeliveryonly
    - require:
      - pkg.installed: postfix-pkgs
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - defaults:
        mailname: {{ grains['fqdn'] }}
        local_networks: {{ local_networks }}

makina-postfix-local-catch-all-delivery-virtual:
  file.managed:
    - name: /etc/postfix/virtual
    - source: salt://makina-states/files/etc/postfix/virtual.localdeliveryonly
    - user: root
    - group: root
    - mode: 644
    - require: 
      - pkg.installed: postfix-pkgs

makina-postfix-aliases-all-to-vagrant-user:
  file.append:
    - name: /etc/aliases
    - require: 
      - pkg.installed: postfix-pkgs
    - text: 
      - "root: vagrant"

# postmap /etc/postfix/virtual when altered
makina-postfix-postmap-virtual-dev:
  cmd.watch:
    - name: postmap /etc/postfix/virtual && echo "" && echo "changed=yes"
    - stateful: True
    - require:
      - pkg.installed: postfix-pkgs
    - watch:
      - file: makina-postfix-local-catch-all-delivery-virtual
# postalias if /etc/aliases is altered
makina-postfix-postalias-dev:
  cmd.watch:
    - stateful: True
    - name: postalias /etc/aliases && echo "" && echo "changed=yes"
    - watch:
      - file: makina-postfix-aliases-all-to-vagrant-user

# ------------ dev mode end -----------------------
{% endif %}


makina-postfix-chroot-hosts-sync:
  cmd.run:
    - unless: diff -q /var/spool/postfix/etc/hosts /etc/hosts
    - stateful: True
    - name: cp -a /etc/hosts /var/spool/postfix/etc/hosts && echo "" && echo "changed=yes"
    - require:
      - pkg.installed: postfix-pkgs

makina-postfix-chroot-localtime-sync:
  cmd.run:
    - unless: diff -q /var/spool/postfix/etc/localtime /etc/localtime
    - stateful: True
    - name: cp -a /etc/localtime /var/spool/postfix/etc/localtime && echo "" && echo "changed=yes"
    - require:
      - pkg.installed: postfix-pkgs

makina-postfix-chroot-nsswitch-sync:
  cmd.run:
    - unless: diff -q /var/spool/postfix/etc/nsswitch.conf /etc/nsswitch.conf 
    - stateful: True
    - name: cp -a /etc/nsswitch.conf  /var/spool/postfix/etc/nsswitch.conf  && echo "" && echo "changed=yes"
    - require:
      - pkg.installed: postfix-pkgs
makina-postfix-chroot-resolvconf-sync:
  cmd.run:
    - unless: diff -q /var/spool/postfix/etc/resolv.conf /etc/resolv.conf
    - stateful: True
    - name: cp -a /etc/resolv.conf /var/spool/postfix/etc/resolv.conf && echo "" && echo "changed=yes"
    - require:
      - pkg.installed: postfix-pkgs

makina-postfix-configuration-check:
  cmd.run:
    - name: /usr/sbin/postfix check 2>&1  && echo "" && echo "changed=no"
    - stateful: True
    - require:
      - pkg.installed: postfix-pkgs
      - cmd: makina-postfix-chroot-hosts-sync
      - cmd: makina-postfix-chroot-resolvconf-sync
      - cmd: makina-postfix-chroot-nsswitch-sync
      - cmd: makina-postfix-chroot-localtime-sync
      # ensure conf files are altered before we check conf
      - file.managed: /etc/postfix/main.cf
{% if grains['makina.nodetype.devhost'] %}
      - file: makina-postfix-aliases-all-to-vagrant-user
      - file: makina-postfix-local-catch-all-delivery-virtual
{% endif %}


#--- MAIN SERVICE RESTART/RELOAD watchers

makina-postfix-service:
  service.running:
    - name: postfix
    - enable: True
    - require:
      - pkg.installed: postfix-pkgs
      - cmd: makina-postfix-configuration-check
    - watch:
      # restart service in case of package install
      - pkg.installed: postfix-pkgs
      # restart service in case of settings alterations
      - file.managed: /etc/postfix/main.cf
      # restart service if /etc/hosts were altered?
      - cmd: makina-postfix-chroot-hosts-sync
{% if grains['makina.nodetype.devhost'] %}
      - cmd: makina-postfix-postmap-virtual-dev
      - cmd: makina-postfix-postalias-dev
{% endif %}

