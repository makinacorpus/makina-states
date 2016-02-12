include:
  - makina-states.services.virt.docker.hooks
  - makina-states.services.virt.cgroups
{%- set locs = salt['mc_locations.settings']() %}
docker-services:
  service.running:
    - name: docker
    - enable: True
    - watch:
      - mc_proxy: docker-pre-hardrestart
    - watch_in:
      - mc_proxy: docker-post-hardrestart

# sometimes docker dies just quick, and relaunching it make things go smooth
docker-restart:
  service.running:
    - name: service docker restart
    - unless: ps aux|egrep -q  -- "docker .*-d"
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
