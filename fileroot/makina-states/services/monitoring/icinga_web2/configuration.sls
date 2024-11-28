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

icingaweb2_nagvis:
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
      - file: icingaweb2_nagvis
{{rmacro()}}


icingaweb2_nagvis-up:
  mc_git.latest:
    - name: https://github.com/corpusops/nagvis.git
    - target: /usr/share/nagvis/nagvis
    - user: root
    - require:
      - mc_git: icingaweb2_nagvis
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
      - mc_git: icingaweb2_nagvis-up
{{rmacro()}}

{% for i, idata in (settings.modules_enabled.items()|list) %}
{% set target=idata.get('target', '/usr/share/icingaweb2/modules/{0}'.format(i)) %}
icingaweb2-config-mod-activate-{{i}}:
  file.symlink:
    - name: /etc/icingaweb2/enabledModules/{{i}}
    - target: "{{target}}"
    - makedirs: true
    - watch:
      - mc_proxy: icinga_web2-pre-conf
      - mc_git: icingaweb2_nagvis
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

{% if settings['modules']['grafana']['enabled'] %}
icingaweb2-install-grafanaplugin:
  cmd.run:
    - name: |-
        set -x
        MODULE_VERSION="{{settings.grafana_icingaplugin_version}}"
        ICINGAWEB_MODULEPATH="{{settings.grafana_icingaplugin_dir}}"
        REPO_URL="https://github.com/Mikesch-mp/icingaweb2-module-grafana"
        TARGET_DIR="${ICINGAWEB_MODULEPATH}/grafana"
        URL="${REPO_URL}/archive/v${MODULE_VERSION}.tar.gz"
        rm -rf $TARGET_DIR
        install -d -m 0755 "${TARGET_DIR}"
        wget -q -O - "$URL" | tar xfz - -C "${TARGET_DIR}" --strip-components 1
    - unless: |-
        set -e
        grep -q "Version: {{settings.grafana_icingaplugin_version}}" "{{settings.grafana_icingaplugin_dir}}/grafana/module.info"
    - watch:
      - cmd: icingaweb2-config-dir
      - mc_proxy: icinga_web2-pre-conf
    - watch_in:
      - mc_proxy: icinga_web2-post-conf
{% endif %}

icingaweb2-patch-logging:
  cmd.run:
    - name: |-
        cd /usr/share/php/
        sed -i -re \
          "s/(error_reporting[(]E_ALL \| E_STRICT)[)]/error_reporting((E_ALL | E_STRICT) \& ~E_DEPRECATED \& ~E_USER_DEPRECATED)/g" \
          Icinga/Application/webrouter.php Icinga/Application/ApplicationBootstrap.php
    - unless: |
        for i in /usr/share/php/Icinga/Application/webrouter.php /usr/share/php/Icinga/Application/ApplicationBootstrap.php;do
          if ( grep -q 'error_reporting(E_ALL | E_STRICT);' $i );then exit 1;fi
        done
    - watch:
      - mc_proxy: icinga_web2-pre-conf
    - watch_in:
      - mc_proxy: icinga_web2-post-conf


