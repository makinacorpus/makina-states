{% set locs=salt['mc_locations.settings']() %}
{{ salt['mc_macros.register']('localsettings', 'etckeeper') }}
include:
  - makina-states.localsettings.etckeeper.hooks
  - makina-states.localsettings.git
{% set defaults = salt['mc_etckeeper.settings']() %}

etckeeper-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - pkgs:
      - git
      - etckeeper
    - watch_in:
      - mc_proxy: etckeeper-inst-pre
    - watch_in:
      - mc_proxy: etckeeper-inst-post


{%- for config, cdata in defaults.configs.items() %}
{% set mode = cdata.get('mode', '0700') %}
etckeeper-{{config}}:
  file.managed:
    - name: {{config}}
    - source : {{cdata.get('template', 'salt://makina-states/files'+config)}}
    - makedirs: True
    - template: jinja
    - user: root
    - group: root
    - mode: 750
    - watch:
      - mc_proxy: etckeeper-conf-pre
    - watch_in:
      - mc_proxy: etckeeper-conf-post
{% endfor %}

etckeeper-initial:
  cmd.run:
    - name: |
            /usr/bin/etckeeper init
            cd /etc
            git config user.email 'makinastates@paas.tld'
            git config user.name 'Makina-States'
            /usr/bin/etckeeper commit "Initial commit"
    - unless: test -d {{locs.conf_dir}}/.git && grep -q user.email /etc/.git/config
    - watch:
      - mc_proxy: etckeeper-run-pre
    - watch_in:
      - mc_proxy: etckeeper-run-hook

etckeeper-perms:
  file.managed:
    - name: {{locs.conf_dir}}/etckeeper/etckeeperperms.sh
    - source: ''
    - user: root
    - group: root
    - mode: 750
    - watch:
      - cmd: etckeeper-initial
    - watch_in:
      - mc_proxy: etckeeper-post-run-hook
    - contents: |
                #!/usr/bin/env bash
                exec {{locs.resetperms }} --dmode 0700 --fmode 0700 --user "root" --group "root" --paths {{locs.conf_dir}}/.git
