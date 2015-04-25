{% set extra_confs = {} %}
include:
  - makina-states.services.virt.virtualbox.hooks
  - makina-states.services.virt.virtualbox.services
{% set extra_confs = {} %}
{% for f, fdata in extra_confs.items() %}
{% set template = fdata.get('template', 'jinja') %}
virtualbox-conf-{{f}}:
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
      - mc_proxy: virtualbox-pre-conf
    - watch_in:
      - mc_proxy: virtualbox-post-conf
{% endfor %}
