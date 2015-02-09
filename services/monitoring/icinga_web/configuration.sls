{#-
# icinga_web
#
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga_web.settings']() %}

include:
  - makina-states.services.monitoring.icinga_web.hooks
  - makina-states.services.monitoring.icinga_web.services

{% for file in ['access',
                'auth',
                'cronks',
                'databases',
                'exclude_customvars',
                'factories',
                'icinga',
                'logging',
                'module_appkit',
                'module_cronks',
                'module_reporting',
                'module_web',
                'settings',
                'sla',
                'translation',
                'userpreferences',
                'views'] %}
icinga_web-{{file}}-conf:
  file.managed:
    - name: {{data.configuration_directory}}/conf.d/{{file}}.xml
    - source: {{data.templates.get(
                   file,
                   'salt://makina-states/files/etc/icinga-web/conf.d/{0}.xml'.format(file))}}
    - template: jinja
    - makedirs: true
    - user: root
    - group: www-data
    - mode: 640
    - watch:
      - mc_proxy: icinga_web-pre-conf
    - watch_in:
      - mc_proxy: icinga_web-post-conf
      - file: icinga_web-usr-cronks-conf
{% endfor %}

# sometimes, the password in /usr/share/icinga-web/config/databases.xml is not updated
# "I noticed that /etc/icinga-web doesn't seem to be parsed. at the very least, /etc/icinga-web/databases.xml doesn't seem to be."
# manually update

icinga_web-usr-database-conf:
  file.managed:
    - names:
      - /usr/share/icinga-web/app/config/databases.xml
      - /etc/icinga-web/conf.d/database-web.xml
    - source: salt://makina-states/files/usr/share/icinga-web/app/config/databases.xml
    - template: jinja
    - makedirs: true
    - user: root
    - group: www-data
    - mode: 644
    - watch:
      - mc_proxy: icinga_web-pre-conf
    - watch_in:
      - mc_proxy: icinga_web-post-conf

icinga_web-usr-cronks-conf:
  file.copy:
    - name: /usr/share/icinga-web/app/config/cronks.xml
    - source: /etc/icinga-web/conf.d/cronks.xml
    - makedirs: true
    - force: True
    - watch:
      - mc_proxy: icinga_web-pre-conf
      - file: icinga_web-cronks-conf
    - watch_in:
      - mc_proxy: icinga_web-post-conf

icinga_web-usr-cronks-2-conf:
  file.managed:
    - name: /usr/share/icinga-web/app/config/cronks.xml
    - user: root
    - group: www-data
    - mode: 644
    - watch:
      - mc_proxy: icinga_web-pre-conf
      - file: icinga_web-usr-cronks-conf
    - watch_in:
      - mc_proxy: icinga_web-post-conf

# clear cache
icinga_web-clear-cache:
  cmd.run:
    - name: rm -f /var/cache/icinga-web/config/*
    - watch:
      - mc_proxy: icinga_web-pre-conf
    - watch_in:
      - mc_proxy: icinga_web-post-conf

# let xml includes resolve absolute path in /etc
icinga_web-etc-sym-connf:
  file.symlink:
    - names:
      - /usr/share/icinga-web/app/config/etc
      - /usr/share/icinga-web/app/modules/AppKit/config/etc
    - target: /etc
    - watch:
      - mc_proxy: icinga_web-pre-conf
    - watch_in:
      - mc_proxy: icinga_web-post-conf

icinga_web-etc-sym-tmpcronks:
  cmd.run:
    - onlyif: test -d /var/cache/icinga-web/tmp && test ! -h /var/cache/icinga-web/tmp
    - name: |
            if [ ! -d /usr/share/icinga-web/tmp ];then
              mkdir -p /usr/share/icinga-web/tmp
            fi
            if [ ! -h /var/cache/icinga-web/tmp ];then
              mv -vf /var/cache/icinga-web/tmp/* /usr/share/icinga-web/tmp
              rm -rf /var/cache/icinga-web/tmp
            fi
  file.symlink:
    - onlyif: test ! -d /var/cache/icinga-web/tmp
    - name: /var/cache/icinga-web/tmp
    - target: /usr/share/icinga-web/tmp
    - watch:
      - cmd: icinga_web-etc-sym-tmpcronks
      - mc_proxy: icinga_web-pre-conf
    - watch_in:
      - mc_proxy: icinga_web-post-conf

# pnp4nagios module
{% if data.modules.pnp4nagios.enabled %}
# add cronks templates
{% for name, template in data.modules.pnp4nagios.cronks_extensions_templates.items() %}
icinga_web-module-pnp4nagios-template-{{name}}-conf:
  file.managed:
    - name: /usr/share/icinga-web/app/modules/Cronks/data/xml/extensions/{{name}}
    - source: {{template}}
    - template: jinja
    - makedirs: true
    - user: root
    - group: www-data
    - mode: 640
    - watch:
      - mc_proxy: icinga_web-pre-conf
    - watch_in:
      - mc_proxy: icinga_web-post-conf
    - defaults:
        data: |
              {{ salt['mc_utils.json_dump'](data) }}
{% endfor %}
{% endif %}
