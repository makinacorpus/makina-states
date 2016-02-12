{% import "makina-states/_macros/h.jinja" as h with context %}
{% set data = salt['mc_postfix.settings']() %}
{% set locs = salt['mc_locations.settings']()%}
include:
  - makina-states.services.mail.postfix.hooks
  - makina-states.services.mail.postfix.services
  - makina-states.localsettings.ssl

{{ locs.conf_dir }}-postfix-dir:
  file.directory:
    - name: {{ locs.conf_dir }}/postfix
    - user: postfix
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: postfix-postinstall
    - watch_in:
      - mc_proxy: postfix-preconf

{{ locs.conf_dir }}-postfix-mailname:
  file.managed:
    - name: {{ locs.conf_dir }}/mailname
    - source: ''
    - contents: {{ data.mailname }}
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: postfix-postinstall
    - watch_in:
      - mc_proxy: postfix-preconf

{{ locs.conf_dir }}-postfix-main.cf:
  file.managed:
    - name: {{ locs.conf_dir }}/postfix/main.cf
    - source: salt://makina-states/files/etc/postfix/main.cf
    - template: jinja
    - user: root
    - group: postfix
    - mode: 644
    - watch:
      - mc_proxy: postfix-preconf
    - watch_in:
      - mc_proxy: postfix-postconf
      - mc_proxy: postfix-prerestart

makina-postfix-chroot-sslconf:
  cmd.run:
    - name: |
        set -e
        rsync -a /etc/ssl/  "{{ locs.var_spool_dir }}/postfix/etc/ssl/"
        echo changed="false"
    - stateful: true
    - watch:
      - mc_proxy: postfix-preconf
    - watch_in:
      - mc_proxy: postfix-postconf
      - mc_proxy: postfix-prerestart

makina-postfix-chroot-hosts-sync:
  cmd.run:
    - unless: diff -q {{ locs.var_spool_dir }}/postfix/etc/hosts {{ locs.conf_dir }}/hosts
    - stateful: True
    - name: cp -a {{ locs.conf_dir }}/hosts {{ locs.var_spool_dir }}/postfix/etc/hosts && echo "" && echo "changed=yes"
    - watch:
      - mc_proxy: postfix-preconf
      - cmd: makina-postfix-chroot-sslconf
    - watch_in:
      - mc_proxy: postfix-postconf
      - mc_proxy: postfix-prerestart

makina-postfix-chroot-localtime-sync:
  cmd.run:
    - unless: diff -q {{ locs.var_spool_dir }}/postfix/etc/localtime {{ locs.conf_dir }}/localtime
    - stateful: True
    - name: cp -a {{ locs.conf_dir }}/localtime {{ locs.var_spool_dir }}/postfix/etc/localtime && echo "" && echo "changed=yes"
    - watch:
      - mc_proxy: postfix-preconf
    - watch_in:
      - mc_proxy: postfix-postconf
      - mc_proxy: postfix-prerestart

makina-postfix-chroot-nsswitch-sync:
  cmd.run:
    - unless: diff -q {{ locs.var_spool_dir }}/postfix/etc/nsswitch.conf {{ locs.conf_dir }}/nsswitch.conf
    - stateful: True
    - name: cp -a {{ locs.conf_dir }}/nsswitch.conf  {{ locs.var_spool_dir }}/postfix/etc/nsswitch.conf  && echo "" && echo "changed=yes"
    - watch:
      - mc_proxy: postfix-preconf
    - watch_in:
      - mc_proxy: postfix-postconf
      - mc_proxy: postfix-prerestart

makina-postfix-chroot-resolvconf-sync:
  cmd.run:
    - unless: diff -q {{ locs.var_spool_dir }}/postfix/etc/resolv.conf {{ locs.conf_dir }}/resolv.conf
    - stateful: True
    - name: cp -a {{ locs.conf_dir }}/resolv.conf {{ locs.var_spool_dir }}/postfix/etc/resolv.conf && echo "" && echo "changed=yes"
    - watch:
      - mc_proxy: postfix-preconf
    - watch_in:
      - mc_proxy: postfix-postconf
      - mc_proxy: postfix-prerestart
makina-postfix-chroot-cacer-sync:
  cmd.run:
    - unless: diff -q {{ locs.var_spool_dir }}/postfix/etc/ssl/certs/ca-certificates.crt {{ locs.conf_dir }}/ssl/certs/ca-certificates.crt
    - stateful: True
    - name: cp -a {{ locs.conf_dir }}/ssl/certs/ca-certificates.crt {{ locs.var_spool_dir }}/postfix/etc/ssl/certs/ca-certificates.crt && echo "" && echo "changed=yes"
    - watch:
      - mc_proxy: postfix-preconf
      - cmd: makina-postfix-chroot-sslconf
    - watch_in:
      - mc_proxy: postfix-postconf
      - mc_proxy: postfix-prerestart
{% macro rmacro() %}
    - watch:
      - mc_proxy: postfix-preconf
    - watch_in:
      - mc_proxy: postfix-postconf
      - cmd: makina-postfix-chroot-sslconf2
{% endmacro %}
{{ h.deliver_config_files(
     data.get('extra_confs', {}),
     after_macro=rmacro,
     prefix='makina-postfix-')}}

makina-postfix-chroot-sslconf2:
  cmd.run:
    - name: |
        set -e
        mkdir "{{ locs.var_spool_dir }}/postfix/etc/postfix" || /bin/true
        rsync -a "/etc/postfix/certificate.pub"  "{{ locs.var_spool_dir }}/postfix/etc/postfix/certificate.pub" || /bin/true
        rsync -a "/etc/postfix/certificate.key"  "{{ locs.var_spool_dir }}/postfix/etc/postfix/certificate.key" || /bin/true
        echo changed="false"
    - stateful: true
    - watch:
      - mc_proxy: postfix-preconf
    - watch_in:
      - mc_proxy: postfix-postconf 

postfix-virtualdir:
  file.directory:
    - name: {{data.virtual_mailbox_base}}
    - user: root
    - group: root
    - mode: 744
    - watch:
      - mc_proxy: postfix-preconf
    - watch_in:
      - mc_proxy: postfix-postconf

{# postalias if {{ locs.conf_dir }}/aliases is altered #}
makina-postfix-postalias:
  cmd.watch:
    - stateful: True
    - name: |
            postalias {{ locs.conf_dir }}/aliases;
            echo "changed=yes"
    - watch:
      - mc_proxy: postfix-postconf
    - watch_in:
      - cmd: makina-postfix-configuration-check

postfix-fixownership:
  cmd.run:
    - name: /usr/bin/ms_resetpostfixperms.sh && echo "changed=false"
    - stateful: true
    - watch:
      - mc_proxy: postfix-postconf
    - watch_in:
      - cmd: makina-postfix-configuration-check

{# postmap when altered #}
{% for f in data.hashtables %}
makina-postfix-postmap-{{f}}:
  cmd.watch:
    - name: |
            cd /etc/postfix;
            postmap hash:/{{locs.conf_dir}}/postfix/{{f}}.local;
            postmap hash:/{{locs.conf_dir}}/postfix/{{f}};
            echo "changed=yes"
    - stateful: True
    - watch:
      - cmd: postfix-fixownership
      - mc_proxy: postfix-postconf
    - watch_in:
      - cmd: makina-postfix-configuration-check
{%endfor %}
