{% if salt['mc_controllers.mastersalt_mode']() %}
{%- set locs = salt['mc_locations.settings']() %}
include:
  - makina-states.services.virt.docker.hooks

docker-repo:
  pkgrepo.managed:
    - name: deb http://get.docker.io/ubuntu docker main
    - file: {{ locs.conf_dir }}/apt/sources.list.d/docker.list
    - key_url: https://get.docker.io/gpg
    - watch:
      - mc_proxy: docker-pre-install
    - watch_in:
      - mc_proxy: docker-post-install

docker-pkgs:
  pkg.{{salt['mc_pkgs.settings']()['installmode']}}:
    - watch:
      - pkgrepo: docker-repo
      - mc_proxy: docker-pre-install
    - watch_in:
      - mc_proxy: docker-post-install
    - pkgs:
      - lxc-docker
{% endif %}
