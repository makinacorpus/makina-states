{#-
# uwsgi
#
# You only need to drop a configuration file in the include dir to add a program.
# Please see the macro at the end of this file.
#}

{% set locs = salt['mc_locations.settings']() %}
{% set data = salt['mc_uwsgi.settings']() %}

include:
  - makina-states.services.proxy.uwsgi.hooks
  - makina-states.services.proxy.uwsgi.services

# startup configuration
{% if grains['os'] in ['Ubuntu'] %}

uwsgi-init-upstart-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/init/uwsgi.conf
    - source: salt://makina-states/files/etc/init/uwsgi.conf
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: uwsgi-pre-conf
    - watch_in:
      - mc_proxy: uwsgi-post-conf
{% endif %}

uwsgi-init-default-conf:
  file.managed:
    - name: {{ locs['conf_dir'] }}/default/uwsgi
    - source: salt://makina-states/files/etc/default/uwsgi
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - mode: 644
    - watch:
      - mc_proxy: uwsgi-pre-conf
    - watch_in:
      - mc_proxy: uwsgi-post-conf


{% set extra_confs = {
  '/usr/bin/uwsgi.sh': {"mode": "755"},
  '/etc/systemd/system/uwsgi.service': {"mode": "644"}
}%}

{% for i, cdata in extra_confs.items() %}
uwsgi-{{i}}:
  file.managed:
    - name: {{i}}
    - source: salt://makina-states/files{{i}}
    - mode: {{cdata.mode}}
    - template: jinja
    - makedirs: true
    - user: root
    - group: root
    - watch:
      - mc_proxy: uwsgi-pre-conf
    - watch_in:
      - mc_proxy: uwsgi-post-conf
{% endfor %}
{%- import "makina-states/services/proxy/uwsgi/macros.jinja" as uwsgi with context %}
{#
{{uwsgi.uwsgiAddWatcher('foo', '/bin/echo', args=[1]) }}
#}
