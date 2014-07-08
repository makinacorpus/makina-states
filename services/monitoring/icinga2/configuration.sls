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
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf
{% endif %}

{#
# add objects configuration
{% import "makina-states/services/monitoring/icinga2/init.sls" as icinga2 with context %}


# clean the objects directory
icinga2-configuration-clean-objects-directory:
  file.directory:
    - name: {{data.objects.directory}}
    - user: root
    - group: root
    - dir_mode: 755
    - makedirs: True
    - clean: True
    - watch:
      - mc_proxy: icinga2-configuration-pre-clean-directories
    - watch_in:
      - mc_proxy: icinga2-configuration-post-clean-directories

# add templates and commands (and contacts, timeperiods...)
{% for name, object in data.objects.objects_definitions.items() %}
    {{ icinga2.configuration_add_object(**object) }}
{% endfor %}
# add autoconfigured hosts
{% for name, object in data.objects.autoconfigured_hosts_definitions.items() %}
    {{ icinga2.configuration_add_auto_host(**object) }}
{% endfor %}
#}

{%- import "makina-states/services/monitoring/icinga2/macros.jinja" as icinga2 with context %}
{#
{{icinga2.icinga2AddWatcher('foo', '/bin/echo', args=[1]) }}
#}
