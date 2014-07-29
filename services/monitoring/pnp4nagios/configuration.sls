{#-
# pnp4nagios
#
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_pnp4nagios.settings']() %}
{% set sdata = salt['mc_utils.json_dump'](data) %}

include:
  - makina-states.services.monitoring.pnp4nagios.hooks
  - makina-states.services.monitoring.pnp4nagios.services

# general configuration
pnp4nagios-conf:
  file.managed:
    - name: {{data.configuration_directory}}/config.php
    - source: salt://makina-states/files/etc/pnp4nagios/config.php
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: pnp4nagios-pre-conf
    - watch_in:
      - mc_proxy: pnp4nagios-post-conf
    - defaults:
      data: |
            {{sdata}}

# icinga configuration
pnp4nagios-icinga-conf:
  file.blockreplace:
    - name: {{data.icinga_cfg.location}}
    - marker_start: "{{data.icinga_cfg.marker_start}}"
    - marker_end: "{{data.icinga_cfg.marker_end}}"
    - show_changes: True
    - watch:
      - mc_proxy: pnp4nagios-pre-conf
    - watch_in:
      - mc_proxy: pnp4nagios-post-conf
    - content: |
               {% for line in data.icinga_cfg.content %}
               {{line}}
               {% endfor %}

# npcd daemon configuration
pnp4nagios-npcd-conf:
  file.managed:
    - name: {{data.configuration_directory}}/npcd.cfg
    - source: salt://makina-states/files/etc/pnp4nagios/npcd.cfg
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: pnp4nagios-pre-conf
    - watch_in:
      - mc_proxy: pnp4nagios-post-conf
    - defaults:
      data: |
            {{sdata}}

# rra configuration
pnp4nagios-rraconf:
  file.managed:
    - name: {{data.configuration_directory}}/rra.cfg
    - source: salt://makina-states/files/etc/pnp4nagios/rra.cfg
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: pnp4nagios-pre-conf
    - watch_in:
      - mc_proxy: pnp4nagios-post-conf
    - defaults:
      data: |
            {{sdata}}

# startup configuration
{% if grains['os'] in ['Ubuntu'] %}
{#
pnp4nagios-npcd-init-upstart-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init/npcd.conf
    - source: salt://makina-states/files/etc/init/npcd.conf
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: pnp4nagios-pre-conf
    - watch_in:
      - mc_proxy: pnp4nagios-post-conf
    - defaults:
      data: |
            {{sdata}}
#}
{% endif %}

pnp4nagios-npcd-init-default-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/default/npcd
    - source: salt://makina-states/files/etc/default/npcd
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: pnp4nagios-pre-conf
    - watch_in:
      - mc_proxy: pnp4nagios-post-conf
    - defaults:
      data: |
            {{sdata}}

pnp4nagios-npcd-init-sysvinit-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init.d/npcd
    - source: salt://makina-states/files/etc/init.d/npcd
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: pnp4nagios-pre-conf
    - watch_in:
      - mc_proxy: pnp4nagios-post-conf
    - defaults:
      data: |
            {{sdata}}



{%- import "makina-states/services/monitoring/pnp4nagios/macros.jinja" as pnp4nagios with context %}
{#
{{png4nagios.pnp4nagiosAddWatcher('foo', '/bin/echo', args=[1]) }}
#}
