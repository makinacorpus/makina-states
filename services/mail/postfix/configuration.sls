{% set postfixSettings = salt['mc_postfix.settings']() %}
{% set locs = salt['mc_locations.settings']()%}
include:
  - makina-states.services.mail.postfix.hooks
  - makina-states.services.mail.postfix.services

{{ locs.conf_dir }}-postfix-dir:
  file.directory:
    - name: {{ locs.conf_dir }}/postfix
    - user: postfix
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: postfix-post-install-hook
    - watch_in:
      - mc_proxy: postfix-pre-conf-hook

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
    - mode: 744
    - watch:
      - mc_proxy: postfix-pre-conf-hook
    - watch_in:
      - mc_proxy: postfix-post-conf-hook
      - mc_proxy: postfix-pre-restart-hook
    - defaults:
      data: |
            {{salt['mc_utils.json_dump'](postfixSettings)}}

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

{% set hashtables = ['virtual_alias_maps', 'networks',
                     'sasl_passwd', 'relay_domains',
                     'transport', 'destinations']%}

{% for f in hashtables %}
makina-postfix-{{f}}:
  file.managed:
    - name: {{ locs.conf_dir }}/postfix/{{f}}
    - source: salt://makina-states/files/etc/postfix/{{f}}
    - user: postfix
    - template: jinja
    - defaults:
      data: |
            {{salt['mc_utils.json_dump'](postfixSettings)}}
    - group: root
    - mode: 740
    - watch:
      - mc_proxy: postfix-pre-conf-hook
    - watch_in:
      - mc_proxy: postfix-post-conf-hook
makina-postfix-local-{{f}}:
  file.managed:
    - name: {{ locs.conf_dir }}/postfix/{{f}}.local
    - source: ''
    - user: postfix
    - group: root
    - mode: 640
    - watch:
      - mc_proxy: postfix-pre-conf-hook
    - watch_in:
      - mc_proxy: postfix-post-conf-hook
{% endfor %}
postfix-virtualdir:
  file.directory:
    - name: {{postfixSettings.virtual_mailbox_base}}
    - user: root
    - group: root
    - mode: 744
    - watch:
      - mc_proxy: postfix-pre-conf-hook
    - watch_in:
      - mc_proxy: postfix-post-conf-hook

{# postalias if {{ locs.conf_dir }}/aliases is altered #}
makina-postfix-postalias:
  cmd.watch:
    - stateful: True
    - name: |
            postalias {{ locs.conf_dir }}/aliases;
            echo "changed=yes"
    - watch:
      - mc_proxy: postfix-post-conf-hook
    - watch_in:
      - cmd: makina-postfix-configuration-check

{# postmap when altered #}
{% for f in hashtables %}
makina-postfix-postmap-{{f}}:
  cmd.watch:
    - name: |
            postmap hash:/{{locs.conf_dir}}/postfix/{{f}}.local;
            postmap hash:/{{locs.conf_dir}}/postfix/{{f}};
            echo "changed=yes"
    - stateful: True
    - watch:
      - mc_proxy: postfix-post-conf-hook
    - watch_in:
      - cmd: makina-postfix-configuration-check
{%endfor %}
