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

{% macro activate_mod(mod) %}
icinga2-{{mod}}-enable:
  cmd.run:
    - name: icinga2-enable-feature {{mod}}
    - unless: test -e /etc/icinga2/features-enabled/{{mod}}.conf
    - watch:
      - mc_proxy: icinga2-templates-gen
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-post-conf
{% endmacro %}

# general configuration
{% for confd in data.icinga_conf.include_recursive %}
{% set confd = data.configuration_directory + '/'+confd|replace('"', '') %}
icinga2-confddefault-rename:
  file.rename:
    - name: {{confd}}.default
    - source: {{confd}}
    - force: true
    - watch:
      - mc_proxy: icinga2-predefault-conf
    - watch_in:
      - mc_proxy: icinga2-pre-conf
    - onlyif: |
              for i in commands.conf downtimes.conf groups.conf hosts notifications.conf services.conf templates.conf timeperiods.conf users.conf;do
                if test -e "{{confd}}/${i}";then exit 0;fi
              done
              exit 1

icinga2-confddefault-recreate-confd:
  file.directory:
    - name: {{confd}}
    - user: root
    - group: root
    - mode: 755
    - force: true
    - makedirs: true
    - watch:
      - file: icinga2-confddefault-rename
    - watch_in:
      - mc_proxy: icinga2-pre-conf
{% endfor %}

{% set modes = {
  '/etc/init.d/icinga2' : 755
} %}

{% set templates = [
  '/etc/init.d/icinga2',
  '/etc/icinga2/icinga2.conf',
  '/etc/icinga2/constants.conf',
  '/etc/default/icinga2',
  '/etc/icinga2/zones.conf'] %}

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

{{activate_mod('ido-'+data.modules.ido2db.database.type)}}
# startup ido2db configuration
{% if grains['os'] in ['Ubuntu'] %}
{% do templates.append('/etc/init.d/ido2db') %}
icinga2-ido2db-init-upstart-conf:
  file.absent:
    - name: {{ locs['conf_dir'] }}/init/ido2db.conf
{% endif %}
{% endif %}

{% for mod in ['livestatus', 'perfdata'] %}
{% if data.modules[mod]['enabled'] %}
{% do templates.append('/etc/icinga2/features-available/{0}.conf'.format(mod)) %}
{{activate_mod(mod)}}
{% endif %}
{% endfor %}

{% for f in templates %}
# constants.conf configuration
icinga2-{{f}}-conf:
  file.managed:
    - name: {{f}}
    - source: salt://makina-states/files{{f}}
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: {{modes.get(f, 644)}}
    - watch:
      - mc_proxy: icinga2-pre-conf
    - watch_in:
      - mc_proxy: icinga2-templates-gen
      - mc_proxy: icinga2-post-conf
    - defaults:
      data: |
            {{sdata}}
{% endfor %}

# add objects configuration
{% import "makina-states/services/monitoring/icinga2/init.sls" as icinga2 with context %}


# add templates and commands (and contacts, timeperiods...)
{% for file, tdata in salt['mc_icinga2.objects']().objects_by_file.items() %}
{% if not file %}
UNCATEGORIZED
{{tdata}}
{%else %}
{% set state_name_salt =  salt['mc_icinga2.replace_chars'](file) %}
icinga2-configuration-{{state_name_salt}}-add-objects-conf:
  file.managed:
    - name: {{data.gen_directory}}/{{file}}
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
{% endif %}
{% endfor %}

{#
### a file per host, abandonned as hard to maintain
### and not performant
## add autoconfigured hosts
#{% for hostname, odata in salt['mc_icinga2.autoconfigured_hosts']().items() %}
## add the host/hostgroup object and its services with only one state (the host and its services are in the same file)
## having all services associated to a host in one file avoid to delete files for disabled services
## the macro configuration_remove_object isn't called so much
#
## the main difference with the previous version, where there was one file per service is that the loops over services
## are done in the template, not in the sls file.
#icinga2-configuration-add-auto-host-conf:
#  file.managed:
#    - name: {{odata.directory}}/{{odata.file}}
#    - source: salt://makina-states/files/etc/icinga2/conf.d/template_auto_configuration_hosts.conf
#    - user: root
#    - group: root
#    - mode: 644
#    - makedirs: True
#    - watch:
#      - mc_proxy: icinga2-configuration-pre-object-conf
#    - watch_in:
#      - mc_proxy: icinga2-configuration-post-object-conf
#    - template: jinja
#    - defaults:
#        hostname: |
#                  {{salt['mc_utils.json_dump'](hostname)}}
#{% endfor %}
#}


# add autoconfigured hosts
# add the host/hostgroup object and its services with only one state (the host and its services are in the same file)
# having all services associated to a host in one file avoid to delete files for disabled services
# the macro configuration_remove_object isn't called so much

# the main difference with the previous version, where there was one file per service is that the loops over services
# are done in the template, not in the sls file.
icinga2-configuration-add-auto-host-confs:
  file.managed:
    - name: {{data.gen_directory}}/autohosts.conf
    - source: salt://makina-states/files/etc/icinga2/conf.d/template_auto_configuration_hosts.conf
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - watch:
      - mc_proxy: icinga2-configuration-pre-object-conf
    - watch_in:
      - mc_proxy: icinga2-configuration-post-object-conf
    - template: jinja

{% for i in [
  '/usr/bin/icinga-service-irc.sh',
  '/usr/bin/icinga-host-irc.sh', 
  '/usr/bin/icinga-service-mail.sh',
  '/usr/bin/icinga-host-mail.sh',
] %}
icinga2-configuration-scripts-{{i}}:
  file.managed:
    - name: {{i}}
    - source: salt://makina-states/files{{i}}
    - user: root
    - group: root
    - mode: 755
    - makedirs: True
    - watch:
      - mc_proxy: icinga2-configuration-pre-object-conf
    - watch_in:
      - mc_proxy: icinga2-configuration-post-object-conf
    - template: jinja
{% endfor%}
