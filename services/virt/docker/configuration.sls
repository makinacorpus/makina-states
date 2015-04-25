{%- set vmdata = salt['mc_cloud_vm.settings']() %}
{%- set data = vmdata.vts.docker %}
{% set extra_confs = {} %} 
include:
  - makina-states.services.virt.docker.hooks
  - makina-states.services.virt.docker.services

{% if salt['mc_controllers.mastersalt_mode']() %}
{% if grains['os'] in ['Ubuntu'] -%}
{% set extra_confs = {'/etc/init/docker-net-makina.conf': {}} %}

{% elif grains['os'] in ['Debian'] -%}
{% set extra_confs = {'/etc/init.d/docker-net-makina': {}} %}
# assume systemd
{% else %}
{% set extra_confs = {'/etc/systemd/system/docker-net-makina.service': {"mode": "644"}} %}
{% endif%}

{% set extra_confs = salt['mc_utils.copy_dictupdate'](
        data['host_confs'],
        extra_confs) %}

{% for f, fdata in extra_confs.items() %}
{% set template = fdata.get('template', 'jinja') %}
docker-conf-{{f}}:
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
      - mc_proxy: docker-pre-conf
    - watch_in:
      - mc_proxy: docker-post-conf
{% endfor %}

{%- set locs = salt['mc_locations.settings']() %}
docker-conf:
  file.managed:
    - name: {{ locs.upstart_dir }}/docker.conf
    - source: salt://makina-states/files/etc/init/docker.conf
    - watch:
      - mc_proxy: docker-pre-conf
    - watch_in:
      - mc_proxy: docker-post-conf
{%endif %}
