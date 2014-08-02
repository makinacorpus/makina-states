{#-
# icinga
#
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_icinga.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

include:
  - makina-states.services.monitoring.icinga.hooks
  - makina-states.services.monitoring.icinga.services

# general configuration
icinga-conf:
  file.managed:
    - name: {{data.configuration_directory}}/icinga.cfg
    - source: salt://makina-states/files/etc/icinga/icinga.cfg
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}

# resource configuration
icinga-resource-conf:
  file.managed:
    - name: {{data.configuration_directory}}/resource.cfg
    - source: salt://makina-states/files/etc/icinga/resource.cfg
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}


# startup configuration
{% if grains['os'] in ['Ubuntu'] %}

icinga-init-upstart-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init/icinga.conf
    - source: salt://makina-states/files/etc/init/icinga.conf
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}

{% endif %}

icinga-init-default-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/default/icinga
    - source: salt://makina-states/files/etc/default/icinga
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}

icinga-init-sysvinit-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init.d/icinga
    - source: salt://makina-states/files/etc/init.d/icinga
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}


# modules configuration
{% if data.modules.cgi.enabled %}
icinga-cgi-conf:
  file.managed:
    - name: {{data.configuration_directory}}/cgi.cfg
    - source: salt://makina-states/files/etc/icinga/cgi.cfg
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}

icinga-cgi-root-account:
  file.managed:
    - name: {{data.configuration_directory}}/htpasswd.users
    - source: ''
    - makedirs: true
    - user: root
    - group: www-data
    - mode: 644
    - contents: ''
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf

  cmd.run:
    - name: if [ -z "$(grep -E '^{{data.modules.cgi.root_account.login}}:' {{data.configuration_directory}}/htpasswd.users)" ]; then htpasswd -b {{data.configuration_directory}}/htpasswd.users {{data.modules.cgi.root_account.login}} {{data.modules.cgi.root_account.password}};  fi;
    - watch:
      - mc_proxy: icinga-pre-conf
      - file: icinga-cgi-root-account
    - watch_in:
      - mc_proxy: icinga-post-conf

icinga-cgi-move-stylesheets:
  file.rename:
    - name: {{data.modules.cgi.absolute_styles_dir}}
    - source: {{data.configuration_directory}}/stylesheets
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf

{% endif %}

{% if data.modules.ido2db.enabled %}

icinga-ido2db-conf:
  file.managed:
    - name: {{data.configuration_directory}}/ido2db.cfg
    - source: salt://makina-states/files/etc/icinga/ido2db.cfg
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}

icinga-idomod-conf:
  file.managed:
    - name: {{data.configuration_directory}}/idomod.cfg
    - source: salt://makina-states/files/etc/icinga/idomod.cfg
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}

# startup ido2db configuration
{% if grains['os'] in ['Ubuntu'] %}

icinga-ido2db-init-upstart-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init/ido2db.conf
    - source: salt://makina-states/files/etc/init/ido2db.conf
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}

{% endif %}

icinga-ido2db-init-sysvinit-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init.d/ido2db
    - source: salt://makina-states/files/etc/init.d/ido2db
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}


{% endif %}

{% if data.modules.mklivestatus.enabled %}

icinga-mklivestatus-conf:
  file.managed:
    - name: {{data.configuration_directory}}/modules/mklivestatus.cfg
    - source: salt://makina-states/files/etc/icinga/modules/mklivestatus.cfg
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf
    - defaults:
      data: |
            {{sdata}}


{% endif %}

# add objects configuration
{% import "makina-states/services/monitoring/icinga/init.sls" as icinga with context %}

# purge objects (the macro add the files into a list)
{% for file in salt['mc_icinga.get_settings_for_object']('purge_definitions') %}
    {{ icinga.configuration_remove_object(file=file) }}
{% endfor %}

# add templates and commands (and contacts, timeperiods...)
{% for name in data.objects.objects_definitions %}
{% set file = salt['mc_icinga.get_settings_for_object']('objects_definitions', name, 'file') %}
    {{ icinga.configuration_add_object(file=file, fromsettings=name) }}
{% endfor %}

# add autoconfigured hosts
{% for name in data.objects.autoconfigured_hosts_definitions %}
{% set hostname = salt['mc_icinga.get_settings_for_object']('autoconfigured_hosts_definitions', name, 'hostname') %}
    {{ icinga.configuration_add_auto_host(hostname=hostname, fromsettings=name) }}
{% endfor %}

# really add the files
{% for file in salt['mc_icinga.add_configuration_object'](get=True) %}
{% set state_name_salt =  salt['mc_icinga.replace_chars'](file) %}
icinga-configuration-{{state_name_salt}}-add-objects-conf:
  file.managed:
    - name: {{data.objects.directory}}/{{file}}
    - source: salt://makina-states/files/etc/icinga/objects/template.cfg
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - watch:
      - mc_proxy: icinga-configuration-pre-object-conf
    - watch_in:
      - mc_proxy: icinga-configuration-post-object-conf
    - template: jinja
    - defaults:
      file: |
            {{salt['mc_utils.json_dump'](file)}}

{% endfor %}

# really delete the files
# if there is a lot of files, it is better to use the "source" argument instead of the "contents" argument
{% set tmpf="/tmp/delete.sh" %}
icinga-configuration-remove-objects-conf:
  file.managed:
    - name: {{tmpf}}
    - source: ''
    - makedirs: true
    - user: root
    - group: root
    -  mode: 755
    - watch:
      - mc_proxy: icinga-configuration-pre-clean-directories
    - watch_in:
      - mc_proxy: icinga-configuration-post-clean-directories
    - contents: |
                #!/bin/bash
                files=({{salt['mc_icinga.remove_configuration_object'](get=True)}});
                for i in "${files[@]}"; do
                    rm -f "$i";
                done;

  cmd.run:
    - name: {{tmpf}}
    - watch:
      - file: icinga-configuration-remove-objects-conf
      - mc_proxy: icinga-configuration-pre-clean-directories
    - watch_in:
      - mc_proxy: icinga-configuration-post-clean-directories

{#
{%- import "makina-states/services/monitoring/icinga/macros.jinja" as icinga with context %}
{{icinga.icingaAddWatcher('foo', '/bin/echo', args=[1]) }}
#}
