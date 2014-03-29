{#-
# RVM integration
# see:
#   - makina-states/doc/ref/formulaes/localsettings/etckeeper.rst
#}

{% set localsettings = salt['mc_localsettings.settings']() %}
{% set locs=salt['mc_localsettings.settings']()['locations'] %}
{% macro do(full=False ) %}
{{ salt['mc_macros.register']('localsettings', 'etckeeper') }}
include:
  - makina-states.localsettings.etckeeper-hooks
{% set defaults = localsettings.etckeeper %}

{% if full %}
etckeeper-pkgs:
  pkg.{{salt['mc_localsettings.settings']()['installmode']}}:
    - pkgs:
      - git
      - etckeeper
    - watch_in:
      - name: etckeeper-initial
      - mc_proxy: etckeeper-run-hook
      - file: etckeeper-conf
{% endif %}

etckeeper-cron:
  file.managed:
    - name: {{locs.conf_dir}}/cron.daily/etckeeper
    - makedirs: True
    - source: salt://makina-states/files/etc/cron.daily/etckeeper
    - template: jinja
    - defaults:
      data: {{defaults|yaml }}
    - user: root
    - group: root
    - mode: 750
    - watch_in:
      - mc_proxy: etckeeper-run-hook

etckeeper-conf:
  file.managed:
    - name: {{locs.conf_dir}}/etckeeper/etckeeper.conf
    - makedirs: True
    - source: salt://makina-states/files/etc/etckeeper/etckeeper.conf
    - template: jinja
    - defaults:
      data: {{defaults|yaml }}
    - user: root
    - group: root
    - mode: 644
    - watch_in:
      - mc_proxy: etckeeper-run-hook

etckeeper-initial:
  cmd.run:
    - name: >
           /usr/bin/etckeeper init;
           /usr/bin/etckeeper commit "Initial commit";
    - require:
       - pkg: etckeeper-pkgs
       - file: etckeeper-conf
    - unless: test -d {{locs.conf_dir}}/.git

etckeeper-perms:
  file.managed:
    - name: {{locs.conf_dir}}/etckeeper/etckeeperperms.sh
    - source: ''
    - user: root
    - group: root
    - mode: 750
    - watch:
      - mc_proxy: etckeeper-run-hook
      - cmd: etckeeper-initial
    - watch_in:
      - mc_proxy: etckeeper-post-run-hook
    - contents: >
                #!/bin/sh

                exec {{locs.resetperms }}
                --dmode 0700 --fmode 0700
                --user "root" --group "root"
                --paths {{locs.conf_dir}}/.git

{# deactivated as soon or later it will be autocommited from
   makina-states.commin.autocommit
etckeeper-run:
  cmd.run:
    - name: {{locs.conf_dir}}/cron.daily/etckeeper "commit from salt"
    - watch:
      - mc_proxy: etckeeper-run-hook
      - cmd: etckeeper-initial
      - file: etckeeper-perms
    - watch_in:
      - mc_proxy: etckeeper-post-run-hook
#}
{% endmacro %}
{{ do(full=False) }}
