{% import "makina-states/_macros/h.jinja" as h with context %}
{% macro rmacro() %}
    - watch:
      - mc_proxy: icinga_web2-pre-conf
    - watch_in:
      - mc_proxy: icinga_web2-post-conf
{% endmacro %}
{#-
# icinga_web2
#
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set settings = salt['mc_icinga_web2.settings']() %}

include:
  - makina-states.services.monitoring.icinga_web2.hooks
  - makina-states.services.monitoring.icinga_web2.services

icingaweb2-config-dir:
  cmd.run:
    - name: icingacli setup config directory
    - unless: test -e /etc/icingaweb2/modules/translation/config.ini
    - watch:
      - mc_proxy: icinga_web2-pre-conf
    - watch_in:
      - mc_proxy: icinga_web2-post-conf

icingaweb2-config-dirs:
  file.directory:
    - names:
      - /etc/icingaweb2/enabledModules
      - /etc/icingaweb2/preferences
    - mode: 750
    - user: www-data
    - group: www-data
    - makedirs: true
    - watch:
      - mc_proxy: icinga_web2-pre-conf
    - watch_in:
      - mc_proxy: icinga_web2-post-conf

icingaweb2_navgis:
  file.directory:
    - name: /usr/share/icingaweb2/modules
    - user: root
    - mode: 755
    - makedirs: true
{{rmacro()}}
  mc_git.latest:
    - name: https://github.com/corpusops/icingaweb2-module-nagvis
    - target: /usr/share/icingaweb2/modules/nagvis
    - user: root
    - require:
      - file: icingaweb2_navgis
{{rmacro()}}


icingaweb2_navgis-up:
  mc_git.latest:
    - name: https://github.com/corpusops/nagvis.git
    - target: /usr/share/nagvis/nagvis
    - user: root
    - require:
      - mc_git: icingaweb2_navgis
  cmd.run:
    - stateful: true
    - name: |-
          cd /usr/share/nagvis
          for i in userfiles;do
            rsync -azv nagvis/share/$i/ share/$i/
          done
          for i in frontend server;do
            rsync -azv --delete nagvis/share/$i/ share/$i/
          done
          echo "changed=no"
    - require:
      - mc_git: icingaweb2_navgis-up
{{rmacro()}}

{% for i, idata in settings.modules_enabled.items()+[('navgis', {})] %}
{% set target=idata.get('target', '/usr/share/icingaweb2/modules/{0}'.format(i)) %}
icingaweb2-config-mod-activate-{{i}}:
  file.symlink:
    - name: /etc/icingaweb2/enabledModules/{{i}}
    - target: "{{target}}"
    - makedirs: true
    - watch:
      - mc_proxy: icinga_web2-pre-conf
      - mc_git: icingaweb2_navgis
      - file: icingaweb2-config-dirs
    - watch_in:
      - mc_proxy: icinga_web2-post-conf
{% endfor %}

icingaweb2-config-token:
  cmd.run:
    - unless: icingacli setup token show
    - name: icingacli setup token create
    - watch:
      - cmd: icingaweb2-config-dir
      - mc_proxy: icinga_web2-pre-conf
    - watch_in:
      - mc_proxy: icinga_web2-post-conf

{{ h.deliver_config_files(
     settings.get('configs', {}),
     mode='644',
     after_macro=rmacro, prefix='icingaweb2-')}}

