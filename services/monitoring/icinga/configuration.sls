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
  file.touch:
    - name: {{data.configuration_directory}}/htpasswd.users

  cmd.run:
    - name: if [ -z "$(grep -E '^icingaadmin:' {{data.configuration_directory}}/htpasswd.users)" ]; then htpasswd -b {{data.configuration_directory}}/htpasswd.users {{data.modules.cgi.root_account.login}} {{data.modules.cgi.root_account.password}};  fi;
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


# test to add configuratipn (MUST BE REMOVED SOON)
{% import "makina-states/services/monitoring/icinga/init.sls" as icinga with context %}

# copy the checks
icinga-configuration-check-ping-plugin:
  file.managed:
    - name: /root/admin_scripts/nagios/check_ping
    - source: salt://makina-states/files/root/admin_scripts/nagios/check_ping
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf

icinga-configuration-check-ssh-plugin:
  file.managed:
    - name: /root/admin_scripts/nagios/check_ssh
    - source: salt://makina-states/files/root/admin_scripts/nagios/check_ssh
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf

icinga-configuration-check-by-ssh-plugin:
  file.managed:
    - name: /root/admin_scripts/nagios/check_by_ssh
    - source: salt://makina-states/files/root/admin_scripts/nagios/check_by_ssh
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf

icinga-configuration-check-disk-plugin:
  file.managed:
    - name: /root/admin_scripts/nagios/check_disk
    - source: salt://makina-states/files/root/admin_scripts/nagios/check_disk
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf

icinga-configuration-check-http-plugins:
  file.managed:
    - name: /root/admin_scripts/nagios/check_http
    - source: salt://makina-states/files/root/admin_scripts/nagios/check_http
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf

icinga-configuration-check-load-plugins:
  file.managed:
    - name: /root/admin_scripts/nagios/check_load
    - source: salt://makina-states/files/root/admin_scripts/nagios/check_load
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf

icinga-configuration-check-dig-plugins:
  file.managed:
    - name: /root/admin_scripts/nagios/check_dig
    - source: salt://makina-states/files/root/admin_scripts/nagios/check_dig
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: icinga-pre-conf
    - watch_in:
      - mc_proxy: icinga-post-conf

# create commands
{{ icinga.configuration_add_object(type='command',
                                   file='commands/ping.cfg',
                                   attrs= {
                                       'command_name': "check-host-alive",
                                       'command_line': "/root/admin_scripts/nagios/check_ping -H '$HOSTADDRESS$' -w 5000,100% -c 5000,100% -p 1",
                                   })
}}
{{ icinga.configuration_add_object(type='command',
                                   file='commands/ssh.cfg',
                                   attrs= {
                                       'command_name': "check_ssh",
                                       'command_line': "/root/admin_scripts/nagios/check_ssh -p '$ARG1$' '$HOSTADDRESS$'",
                                   })
}}
{{ icinga.configuration_add_object(type='command',
                                   file='commands/check_by_ssh_mountpoint.cfg',
                                   attrs= {
                                       'command_name': "check_by_ssh_mountpoint",
                                       'command_line': "/root/admin_scripts/nagios/check_by_ssh -q -l '$ARG1$' -H '$ARG2$' -p '$ARG3$'  -C '/root/admin_scripts/nagios/check_disk \"$ARG4$\" -w \"$ARG5$\" -c \"$ARG6$\"'",
                                   })
}}
# check_http already defined in /etc/nagios-plugins/config/http.cfg
{{ icinga.configuration_add_object(type='command',
                                   file='commands/http.cfg',
                                   attrs= {
                                       'command_name': "check_http",
                                       'command_line': "/root/admin_scripts/nagios/check_http '$HOSTADDRESS$'",
                                   })
}}
{{ icinga.configuration_add_object(type='command',
                                   file='commands/check_by_ssh_cpuload.cfg',
                                   attrs= {
                                       'command_name': "check_by_ssh_cpuload",
                                       'command_line': "/root/admin_scripts/nagios/check_by_ssh -q -l '$ARG1$' -H '$ARG2$' -p '$ARG3$'  -C '/root/admin_scripts/nagios/check_load -w \"$ARG4$\" -c \"$ARG5$\"'",
                                   })
}}
{{ icinga.configuration_add_object(type='command',
                                   file='commands/check_dig.cfg',
                                   attrs= {
                                       'command_name': "check_dig",
                                       'command_line': "/root/admin_scripts/nagios/check_dig -T '$ARG1$' -l '$ARG2$' -a '$ARG3$'",
                                   })
}}



{{ icinga.configuration_add_auto_host(hostname='hostname1',
                                   attrs={
                                            'host_name': "hostname1",
                                            'use': "generic-host",
                                            'alias': "host1 generated with salt",
                                            'address': "127.127.0.1",
                                         },
                                   ssh_user='root',
                                   ssh_addr='127.127.0.1',
                                   ssh_port=22,
                                  ) }}


{{ icinga.configuration_add_auto_host(hostname='hostname2',
                                   attrs={
                                            'host_name': "hostname2",
                                            'use': "generic-host",
                                            'alias': "host2 generated with salt",
                                            'address': "127.127.0.2",
                                         },
                                   ssh_user='root',
                                   ssh_addr='127.127.0.2',
                                   ssh_port=22
                                  ) }}


{#
{{ icinga.configuration_edit_object(type='service', name='SSH', attr='host_name', value='hostname1') }}
{{ icinga.configuration_edit_object(type='service', name='SSH', attr='host_name', value='hostname2') }}
#}


{%- import "makina-states/services/monitoring/icinga/macros.jinja" as icinga with context %}
{#
{{icinga.icingaAddWatcher('foo', '/bin/echo', args=[1]) }}
#}
