#
# Should be preconfigured on ubuntu precise
# as the default conf will prevent the daemon to start on a container
#
{% set data = salt['mc_ulogd.settings']() %}
include:
  - makina-states.services.log.ulogd.hooks
{% if salt['mc_controllers.allow_lowlevel_states']() %}
  - makina-states.services.log.ulogd.services

makina-ulogd-configuration-check:
  cmd.run:
    - name: /bin/true && echo "changed=no"
    - stateful: true
    - watch:
      - mc_proxy: ulogd-post-conf-hook
    - watch_in:
      - mc_proxy: ulogd-pre-restart-hook

{% for f, fdata in data.confs.items() %}
{% set template = fdata.get('template', 'jinja') %}
makina-ulogd-{{f}}:
  file.managed:
    - name: "{{fdata.get('target', f)}}"
    - source: "{{fdata.get('source', 'salt://makina-states/files'+f)}}"
    - mode: "{{fdata.get('mode', 750)}}"
    - user: "{{fdata.get('user', 'root')}}"
    - group:  "{{fdata.get('group', 'root')}}"
    {% if fdata.get('makedirs', True) %}
    - makedirs: true
    {% endif %}
    {% if template %}
    - template: "{{template}}"
    {%endif%}
    - watch:
      - mc_proxy: ulogd-pre-conf-hook
    - watch_in:
      - mc_proxy: ulogd-post-conf-hook
{%endfor %}
{%endif %}
