{% import "makina-states/_macros/h.jinja" as h with context %}
#
# You only need to drop a configuration file in the include dir to add a watcher.
# Please see the circusAddWatcher macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set defaults = salt['mc_circus.settings']() %}
{%- set venv = defaults['venv'] %}
{% set adata = salt['mc_icinga2.settings']() %}

{% import "makina-states/localsettings/users/init.sls" as user with context %}
{% import "makina-states/services/monitoring/circus/macros.jinja" as circus with context %}

include:
  - makina-states.services.monitoring.icinga2.hooks
{#
  - makina-states.services.monitoring.circus
  - makina-states.localsettings.users.hooks

icinga2-bot-packages:
  pkg.installed:
    - pkgs:
      - supybot
    - watch:
      - mc_proxy: icinga2-pre-conf
      - mc_proxy: users-ready-hook
    - watch_in:
      - mc_proxy: circus-post-conf
      - mc_proxy: icinga2-post-conf

{% set extra_confs = {
     '/etc/logrotate.d/icinga_supybot.conf': {'mode': '644'},
     '/home/users/icinga_supybot/makina_icinga.conf': {
       'user':  'icinga_supybot',
       'group': 'icinga_supybot',
       'mode': '740'}
       } %}
{% macro rmacro() %}
    - watch:
      - mc_proxy: icinga2-pre-conf
      - mc_proxy: users-ready-hook
    - watch_in:
      - mc_proxy: circus-post-conf
      - mc_proxy: icinga2-post-conf
{% endmacro %}
{{ h.deliver_config_files(extra_confs, after_macro=rmacro, prefix='icinga2-bot-conf-')}}

{% for f in ['/home/users/icinga_supybot/backup',
             '/home/users/icinga_supybot/conf',
             '/home/users/icinga_supybot/data',
             '/home/users/icinga_supybot/logs',
             '/home/users/icinga_supybot/plugins',
             '/home/users/icinga_supybot/tmp'] %}
icinga2-bot-{{f}}:
  file.recurse:
    - name: {{f}}
    - source: salt://makina-states/files{{f}}
    - dir_mode: 750
    - file_mode: 740
    - makedirs: true
    - force: true
    - template: jinja
    - user: icinga_supybot
    - group: icinga_supybot
    - watch:
      - mc_proxy: icinga2-pre-conf
      - mc_proxy: users-ready-hook
    - watch_in:
      - mc_proxy: circus-post-conf
      - mc_proxy: icinga2-post-conf
{% endfor %}

{% if adata.irc.enabled %}
{% set circus_data = {
  'cmd': 'supybot makina_icinga.conf',
  'environment': {},
  'uid': 'icinga_supybot',
  'gid': 'icinga_supybot',
  'copy_env': True,
  'working_dir': '/home/users/icinga_supybot',
  'warmup_delay': "10",
  'max_age': 24*60*60} %}
{{ circus.circusAddWatcher('icinga_supybot', **circus_data) }}
{% else %}
icinga2-disable-ircbot:
  file.absent:
    - names:
      - /etc/circus/circusd.conf.d/100_watcher-icinga_supybot.ini
      - /etc/logrotate.d/icinga_supybot.ini
    - watch_in:
      - mc_proxy: icinga2-post-conf
{% endif %}
#}
