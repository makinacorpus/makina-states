{% if salt['mc_controllers.mastersalt_mode']() %}
include:
  - makina-states.services.virt.docker.hooks
  - makina-states.services.virt.cgroups
{%- set locs = salt['mc_locations.settings']() %}
docker-services:
  service.running:
    - names:
      - docker
      - docker-net-makina
    - enable: True
    - watch:
      - mc_proxy: docker-pre-hardrestart
    - watch_in:
      - mc_proxy: docker-post-hardrestart

docker-restart:
  cmd.run:
    - name: |
            set -e
            service docker restart
            touch {{ locs.conf_dir }}/.docker-installed
    - unless: ps aux|grep -q -- "docker -d -r"
    - require:
      - service: docker-services
    - require_in:
      - mc_proxy: docker-post-inst
{% for i in ['ubuntu'] %}
docker-preload-images-{{i.replace(':', '-')}}:
  docker.pulled:
    - name: "{{i}}"
    - require:
      - service: docker-services
    - require_in:
      - mc_proxy: docker-post-inst
{% endfor %}
{% endif %}
