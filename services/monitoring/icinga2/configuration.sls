{#-
# icinga2
#
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga2.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

include:
  - makina-states.services.monitoring.icinga2.hooks
  - makina-states.services.monitoring.icinga2.services

# general configuration
{% set confd = data.configuration_directory + '/conf.d' %}
icinga2-confddefault-rename:
  file.rename:
    - name: {{confd}}.default
    - source: {{confd}}
    - user: root
    - group: root
    - mode: 644
    - force: true
    - watch:
      - mc_proxy: icinga2-predefault-conf
    - watch_in:
      - mc_proxy: icinga2-pre-conf
    - onlyif: |
              for i in commands.conf downtimes.conf groups.conf hosts notifications.conf salt_generated services.conf templates.conf timeperiods.conf users.conf;do
                if test -e "{{confd}}/${i}";then exit 0;fi
              done
              exit 1

icinga2-conf:
  file.managed:
    - name: {{data.configuration_directory}}/icinga2.conf
    - source: salt://makina-states/files/etc/icinga2/icinga2.conf
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf
    - defaults:
      data: |
            {{sdata}}

# constants.conf configuration
icinga2-constants-conf:
  file.managed:
    - name: {{data.configuration_directory}}/constants.conf
    - source: salt://makina-states/files/etc/icinga2/constants.conf
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf
    - defaults:
      data: |
            {{sdata}}

# constants.conf configuration
icinga2-zones-conf:
  file.managed:
    - name: {{data.configuration_directory}}/zones.conf
    - source: salt://makina-states/files/etc/icinga2/zones.conf
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf
    - defaults:
      data: |
            {{sdata}}

# startup configuration
{#
# I don't have succeeded to write a correct upstart script
{% if grains['os'] in ['Ubuntu'] %}
icinga2-init-upstart-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init/icinga2.conf
    - source: salt://makina-states/files/etc/init/icinga2.conf
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf
    - defaults:
      data: |
            {{sdata}}
{% endif %}
#}

icinga2-init-default-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/default/icinga2
    - source: salt://makina-states/files/etc/default/icinga2
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf
    - defaults:
      data: |
            {{sdata}}

icinga2-init-sysvinit-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init.d/icinga2
    - source: salt://makina-states/files/etc/init.d/icinga2
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf
    - defaults:
      data: |
            {{sdata}}

# modules configuration
{% if data.modules.cgi.enabled %}
icinga2-cgi-conf:
  file.managed:
    - name: {{data.configuration_directory}}/classicui/cgi.cfg
    - source: salt://makina-states/files/etc/icinga2/classicui/cgi.cfg
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf
    - defaults:
      data: |
            {{sdata}}

icinga2-cgi-root-account:
  file.touch:
    - name: {{data.configuration_directory}}/classicui/htpasswd.users

  cmd.run:
    - name: if [ -z "$(grep -E '^{{data.modules.cgi.root_account.login}}:' {{data.configuration_directory}}/classicui/htpasswd.users)" ]; then htpasswd -b {{data.configuration_directory}}/classicui/htpasswd.users {{data.modules.cgi.root_account.login}} {{data.modules.cgi.root_account.password}};  fi;
    - watch:
      - mc_proxy: icinga2-pre-conf
      - file: icinga2-cgi-root-account
    - watch_in:
      - mc_proxy: icinga2-post-conf

icinga2-cgi-move-stylesheets:
  file.rename:
    - name: {{data.modules.cgi.absolute_styles_dir}}
    - source: {{data.configuration_directory}}/classicui/stylesheets
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf

icinga2-cgi-link-stylesheets:
  file.symlink:
    - name: {{data.modules.cgi.nginx.doc_root}}/stylesheets
    - target: {{data.modules.cgi.absolute_styles_dir}}
    - watch:
      - mc_proxy: icinga2-pre-conf
      - file: icinga2-cgi-move-stylesheets
    - watch_in:
      - mc_proxy: icinga2-post-conf

{% endif %}

{% if data.modules.ido2db.enabled %}

icinga2-ido2db-conf:
  file.managed:
    - name: {{data.configuration_directory}}/features-available/ido-{{data.modules.ido2db.database.type}}.conf
    - source: salt://makina-states/files/etc/icinga2/features-available/ido-{{data.modules.ido2db.database.type}}.conf
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf
    - defaults:
      data: |
            {{sdata}}

icinga2-ido2db-enable:
  cmd.run:
    - name: icinga2-enable-feature ido-{{data.modules.ido2db.database.type}}
    - unless: test -e /etc/icinga2/features-enabled/ido-pgsql.conf
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf


# startup ido2db configuration
{% if grains['os'] in ['Ubuntu'] %}
icinga2-ido2db-init-upstart-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init/ido2db.conf
    - source: salt://makina-states/files/etc/init/ido2db.conf
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf
    - defaults:
      data: |
            {{sdata}}
{% endif %}

icinga2-ido2db-init-sysvinit-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init.d/ido2db
    - source: salt://makina-states/files/etc/init.d/ido2db
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf
    - defaults:
      data: |
            {{sdata}}

{% endif %}

{% if data.modules.mklivestatus.enabled %}
icinga2-mklivestatus-enable:
  cmd.run:
    - name: icinga2-enable-feature livestatus
    - unless: test -e /etc/icinga2/features-enabled/livestatus.conf
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf
{% endif %}

# add objects configuration
{% import "makina-states/services/monitoring/icinga2/init.sls" as icinga2 with context %}

# purge objects (the macro add the files into a list)
{% for file in salt['mc_icinga2.get_settings_for_object']('purge_definitions') %}
    {{ icinga2.configuration_remove_object(file=file) }}
{% endfor %}

# add templates and commands (and contacts, timeperiods...)
{% for name in data.objects.objects_definitions %}
{% set file = salt['mc_icinga2.get_settings_for_object']('objects_definitions', name, 'file') %}
    {{ icinga2.configuration_add_object(file=file, fromsettings=name) }}
{% endfor %}

# add autoconfigured hosts
{% for name in data.objects.autoconfigured_hosts_definitions %}
{% set hostname = salt['mc_icinga2.get_settings_for_object']('autoconfigured_hosts_definitions', name, 'hostname') %}
    {{ icinga2.configuration_add_auto_host(hostname=hostname, fromsettings=name) }}
{% endfor %}

# really add the files
{% for file in salt['mc_icinga2.add_configuration_object'](get=True) %}
{% set state_name_salt =  salt['mc_icinga2.replace_chars'](file) %}
icinga2-configuration-{{state_name_salt}}-add-objects-conf:
  file.managed:
    - name: {{data.objects.directory}}/{{file}}
    - source: salt://makina-states/files/etc/icinga2/conf.d/template.conf
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - watch:
      - mc_proxy: icinga2-configuration-pre-object-conf
    - watch_in:
      - mc_proxy: icinga2-configuration-post-object-conf
    - template: jinja
    - defaults:
      file: |
            {{salt['mc_utils.json_dump'](file)}}

{% endfor %}

# really delete the files
# if there is a lot of files, it is better to use the "source" argument instead of the "contents" argument
{% set tmpf="/tmp/delete.sh" %}
icinga2-configuration-remove-objects-conf:
  file.managed:
    - name: {{tmpf}}
    - source: ''
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga2-configuration-pre-clean-directories
    - watch_in:
      - mc_proxy: icinga2-configuration-post-clean-directories
    - contents: |
                #!/bin/bash
                files=({{salt['mc_icinga2.remove_configuration_object'](get=True)}});
                for i in "${files[@]}"; do
                    rm -f "$i";
                done;
  cmd.run:
    - name: {{tmpf}}
    - watch:
      - file: icinga2-configuration-remove-objects-conf
      - mc_proxy: icinga2-configuration-pre-clean-directories
    - watch_in:
      - mc_proxy: icinga2-configuration-post-clean-directories
