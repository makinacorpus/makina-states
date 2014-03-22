{#- Postfix SMTP Server managment #}
{% macro do(full=True) %}
{% import "makina-states/_macros/services.jinja" as services with context %}
{{ salt['mc_macros.register']('services', 'mail.postfix') }}
{% set localsettings = services.localsettings %}
{% set nodetypes = services.nodetypes %}
{% set postfixSettings = salt['mc_postfix.settings']() %}
{% set locs = salt['mc_localsettings']()['locations'] %}
include:
  - makina-states.services.mail.postfix-hooks

{% if full %}
postfix-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - postfix
      - postfix-pcre
    - watch:
      - mc_proxy: postfix-pre-install-hook
    - watch_in:
      - mc_proxy: postfix-post-install-hook
{% endif %}

 
{{ locs.conf_dir }}-postfix-mailname:
  file.managed:
    - name: {{ locs.conf_dir }}/mailname
    - source: ''
    - contents: {{ postfixSettings.mailname }}
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: postfix-post-install-hook
    - watch_in:
      - mc_proxy: postfix-pre-conf-hook

{{ locs.conf_dir }}-postfix-main.cf:
  file.managed:
    - name: {{ locs.conf_dir }}/postfix/main.cf
    - source: salt://makina-states/files/etc/postfix/main.cf
    - template: jinja
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: postfix-pre-conf-hook
    - watch_in:
      - mc_proxy: postfix-post-conf-hook
      - mc_proxy: postfix-pre-restart-hook
    - defaults: {{postfixSettings|yaml}}

makina-postfix-chroot-hosts-sync:
  cmd.run:
    - unless: diff -q {{ locs.var_spool_dir }}/postfix/etc/hosts {{ locs.conf_dir }}/hosts
    - stateful: True
    - name: cp -a {{ locs.conf_dir }}/hosts {{ locs.var_spool_dir }}/postfix/etc/hosts && echo "" && echo "changed=yes"
    - watch:
      - mc_proxy: postfix-pre-conf-hook
    - watch_in:
      - mc_proxy: postfix-post-conf-hook
      - mc_proxy: postfix-pre-restart-hook

makina-postfix-chroot-localtime-sync:
  cmd.run:
    - unless: diff -q {{ locs.var_spool_dir }}/postfix/etc/localtime {{ locs.conf_dir }}/localtime
    - stateful: True
    - name: cp -a {{ locs.conf_dir }}/localtime {{ locs.var_spool_dir }}/postfix/etc/localtime && echo "" && echo "changed=yes"
    - watch:
      - mc_proxy: postfix-pre-conf-hook
    - watch_in:
      - mc_proxy: postfix-post-conf-hook
      - mc_proxy: postfix-pre-restart-hook

makina-postfix-chroot-nsswitch-sync:
  cmd.run:
    - unless: diff -q {{ locs.var_spool_dir }}/postfix/etc/nsswitch.conf {{ locs.conf_dir }}/nsswitch.conf
    - stateful: True
    - name: cp -a {{ locs.conf_dir }}/nsswitch.conf  {{ locs.var_spool_dir }}/postfix/etc/nsswitch.conf  && echo "" && echo "changed=yes"
    - watch:
      - mc_proxy: postfix-pre-conf-hook
    - watch_in:
      - mc_proxy: postfix-post-conf-hook
      - mc_proxy: postfix-pre-restart-hook

makina-postfix-chroot-resolvconf-sync:
  cmd.run:
    - unless: diff -q {{ locs.var_spool_dir }}/postfix/etc/resolv.conf {{ locs.conf_dir }}/resolv.conf
    - stateful: True
    - name: cp -a {{ locs.conf_dir }}/resolv.conf {{ locs.var_spool_dir }}/postfix/etc/resolv.conf && echo "" && echo "changed=yes"
    - watch:
      - mc_proxy: postfix-pre-conf-hook
    - watch_in:
      - mc_proxy: postfix-post-conf-hook
      - mc_proxy: postfix-pre-restart-hook

{# postalias if {{ locs.conf_dir }}/aliases is altered #}
makina-postfix-postalias:
  cmd.watch:
    - stateful: True
    - name: postalias {{ locs.conf_dir }}/aliases;echo "changed=yes"
    - watch:
      - mc_proxy: postfix-pre-conf-hook
    - watch_in:
      - mc_proxy: postfix-post-conf-hook
      - mc_proxy: postfix-pre-restart-hook

makina-postfix-virtual:
  file.managed:
    - name: {{ locs.conf_dir }}/postfix/virtual
    - source: salt://makina-states/files/etc/postfix/virtual
    - user: root
    - template: jinja
    - defaults: {{postfixSettings|yaml}}
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: postfix-pre-conf-hook
    - watch_in:
      - mc_proxy: postfix-post-conf-hook

{# postmap /etc/postfix/virtual when altered #}
makina-postfix-postmap-virtual:
  cmd.watch:
    - name: |
            postmap {{ locs.conf_dir }}/postfix/virtual;
            echo "changed=yes"
    - stateful: true
    - watch:
      - file: makina-postfix-virtual
      - mc_proxy: postfix-pre-conf-hook
    - watch_in:
      - mc_proxy: postfix-post-conf-hook
      - mc_proxy: postfix-pre-restart-hook

{% if postfixSettings.auth %}
fill-/etc/postfix/sasl_passwd:
  file.managed:
    - name: {{locs.conf_dir}}/postfix/sasl_passwd
    - mode: 700
    - user: root
    - group: root
    - source: ''
    - contents: '[{{postfixSettings.relay_host}}]:{{postfixSettings.relay_port}} {{postfixSettings.auth_user}}:{{postfixSettings.auth_password}}'

makina-postfix-postmap-sasl:
  cmd.watch:
    - name: |
            postmap {{ locs.conf_dir }}/postfix/sasl_passwd;
            echo "changed=yes"
    - stateful: True
    - watch:
      - file: fill-/etc/postfix/sasl_passwd
      - mc_proxy: postfix-pre-conf-hook
    - watch_in:
      - mc_proxy: postfix-post-conf-hook
      - mc_proxy: postfix-pre-restart-hook
{% endif %}

makina-postfix-configuration-check:
  cmd.run:
    - name: {{ locs.sbin_dir }}/postfix check 2>&1  && echo "" && echo "changed=no"
    - stateful: True
    - watch:
      - mc_proxy: postfix-post-conf-hook
    - watch_in:
      - mc_proxy: postfix-pre-restart-hook

makina-postfix-service:
  service.running:
    - name: postfix
    - enable: True
    - watch_in:
      - mc_proxy: postfix-post-restart-hook
    - watch:
      - mc_proxy: postfix-pre-restart-hook
{% endmacro %}
{{ do(full=False) }}
