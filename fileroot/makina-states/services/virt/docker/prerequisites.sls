{%- set locs = salt['mc_locations.settings']() %}
{%- set vmdata = salt['mc_cloud_vm.settings']() %}
{%- set data = vmdata.vts.docker %}
include:
  - makina-states.services.virt.docker.hooks

docker-repo:
  pkgrepo.managed:
    - retry: {attempts: 6, interval: 10}
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
    - pkgs: [lxc-docker-{{data.docker_version}}]

ms-dockerviz:
  file.managed:
    - user: root
    - group: root
    - mode: 755
    - name: /usr/bin/dockviz
    - source: https://github.com/justone/dockviz/releases/download/v0.2/dockviz_linux_amd64
    - source_hash: md5=bb4e629a7a09db7c3ac2e7b824fa405d
    - watch:
      - mc_proxy: docker-pre-install
    - watch_in:
      - mc_proxy: docker-post-install
