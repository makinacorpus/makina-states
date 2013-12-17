#
# Easy managment of dockers via pillar
# {# THIS IS AN UNFINISHED WORK IN PROGRESS #}
#
#

# To configure a global registry use this:
#
# docker-settings:
#   repository:
#     login: xxx
#     passwd: xxx
#     url: https://docker-index.makina-corpus.net

# To create docker guests:
# define in pillar an entry "*-docker-server-def
# you need at least to define either image or url
# as:
#
# toto-docker-server-def:
#   - image (opt) : docker image to use
#   - url (opt): git repo where to find dockerfile
#
# If you use url, you have also those params:
#   - branch: branch in the git repo where to find the dockerfile
#   - docker-dir: directory in the branch where is the dockerfile
#   - url (opt): git repo where to find dockerfile
#
# Ports configuration:
#   - ports:
#     fromhost: inguest
#
# Volumes configuration:
#   - DirectoryInHost: MountpointInGuest
#
# Examples:
# project1-docker-servers-def:
#   dockers:
#     prod:
#       url: git+ssh://monprojet
#       branch: php-prod
#       count: 4
#       ports:
#         9080: 80 # dans ce cas pour le nat, on incremente les redirs, genre 1ere instance 8080->80 2eme 8081->81
#         4322: 22
#     dev-1:
#       url: git+ssh://monprojet # branche par default donc 'salt'
#       ports:
#         8080: 80
#         4222: 22
#     db-1:
#       image: makinacorpus/postgresql  # image docker
#       volumes:
#         /dockers/p1/data: /mnt/data/data #pour la forme, purement optionnel puisque le host survit au shutdown
#       ports:
#         4223: 22
#     db-dev:
#       image: makinacorpus/postgresql
#       volumes:
#         /dockers/p1/data: /mnt/data/data #pour la forme, purement optionnel puisque le host survit au shutdown
#       ports:
#         4225: 22
#     reverseproxy-1:
#       url: git+ssh://monprojet
#       branch: varnish
#       volumes:
#         /dockers/p1/data: /mnt/data/data #pour la forme, purement optionnel puisque le host survit au shutdown
#       ports:
#         4224: 22
#
# and it will create a docker guest for you

{% import "makina-states/_macros/services.jinja" as services with context %}
{{ services.register('virt.docker') }}
{% set localsettings = services.localsettings %}
{% set locs = localsettings.locations %}

docker-repo:
  pkgrepo.managed:
    - name: deb http://get.docker.io/ubuntu docker main
    - file: {{ locs.conf_dir }}/apt/sources.list.d/docker.list
    - key_url: https://get.docker.io/gpg

# require dockerpy in salt

docker-pkgs:
  pkg.installed:
    - require:
      - pkgrepo: docker-repo
    - pkgs:
      - lxc-docker

docker-conf:
  file.managed:
    - name: {{ locs.upstart_dir }}/docker.conf
    - source: salt://makina-states/files/etc/init/docker.conf
    - require_in:
      - service: docker-services

# restart on first run with new init script
docker-restart:
  cmd.run:
    - name: service docker restart;touch {{ locs.conf_dir }}/.docker-installed
    - unless: ps aux|grep -q -- "docker -d -r"
    - require:
      - service: docker-services

docker-services:
  service.running:
    - require:
      - pkg: docker-pkgs
      - file: docker-conf
    - enable: True
    - names:
      - docker

docker-preload-images:
  cmd.run:
    - name: for i in ubuntu;do docker pull $i;done
    - require:
      - service: docker-services

# as it is often a mount -bind, we must ensure we can attach dependencies there
# set in pillar:
# makina.localsettings.docker_root: real dest
{% set docker_dir = locs.docker_root %}
{% set dockerSysRoot = locs.var_lib_dir+'/docker' %}
docker-root:
  file.directory:
    - name: {{ dockerSysRoot }}

{% if docker_dir %}
docker-dir:
  file.directory:
    - name: {{ docker_dir }}

docker-mount:
  mount.mounted:
    - require:
      - file: docker-dir
    - name: {{ dockerRoot }}
    - device: {{ docker_dir }}
    - fstype: none
    - mkmnt: True
    - opts: bind
    - require:
      - file: docker-root
      - file: docker-dir
    - require_in:
      - file: docker-after-maybe-bind-root
{% endif %}

docker-after-maybe-bind-root:
  file.directory:
    - name: {{locs.var_lib_dir}}/docker
    - require_in:
      - pkg: docker-pkgs
    - require:
      - file: docker-root

{% set dkey='-docker-servers-def' %}
{% for did, dockers_data in pillar.items() %}
  {% if did.endswith(dkey) %}
    {% for cid, data in dockers_data.get('dockers', {}).items() %}
      {% set pre=did.split(dkey)[0] %}
      {% set id = pre+'-'+cid %}
      {% set image=data.get('image', False) %}
      {% set hostname=data.get('hostname', id) %}
      {% set url=data.get('url', False) %}
      {% set count=data.get('count', '1')|int %}
      {% set volumes=data.get('volumes', {}).items() %}
      {% set docker_dir = data.get('docker-dir', '.') %}
      {% set ports=data.get('ports', {}).items() %}
      {% set branch=data.get('branch', 'salt')  %}
      {% set volumes_passed=[] %}
      {% if volumes %}
        {% for mountpoint, volume in volumes %}
          {%- if not mountpoint in volumes_passed %}
            {% do volumes_passed.append(mountpoint) %}
          {% endif -%}
docker-volume-{{ mountpoint }}:
  file.directory:
    - name: {{ mountpoint }}
        {% endfor %}
      {% endif %}
# donnerait 'project-prod-1 project-dev-1 project-db-dev, ...'
      {% for instancenum in range(count) %}
        {% set instancenumstr=''%}
        {% if count > 1 %}
          {% set instancenumstr = '_%s' % instancenum %}
        {% endif %}
docker-{{ id }}{{ instancenumstr }}:
        {% if not image %}
  mc_git.latest:
    - name: {{ url }}
    - rev: remotes/origin/{{ branch }}
    - target: locs.srv_dir/dockers-repo-cache/dockers-{{ id }}
        {% endif %}
  dockerio.installed:
    - hostname: {{ hostname }}
    - docker_dir: {{ docker_dir }}
        {% if volumes_passed or not image %}
    - require:
          {% for v in volumes_passed %}
        - file.directory: {{ v }}
          {% endfor %}
          {% if not image %}
        - mc_git: docker-{{ id }}
          {% endif %}
        {% endif %}
        {% if image %}
    - image: {{ image }}
          {% else %}
    - path: locs.srv_dir/dockers-repo-cache/dockers-{{ id }}
        {% endif %}
        {% if ports %}
    - ports:
          {% for host_port, container_port in  ports %}
      {% set host_port=host_port|int %}
      {% set host_port=container_port|int %}
      - {{host_port + instancenum - 1}}: {{container_port + instancenum - 1}}
          {% endfor %}
        {% endif %}
        {% if volumes %}
    - require_in:
      - cmd: docker-post-inst
    - volumes:
          {% for mountpoint, volume in  volumes %}
      - {{ mountpoint }}: {{ volume }}
          {% endfor %}
        {% endif %}
      {% endfor %}
    {% endfor %}
  {% endif %}
{% endfor %}

docker-post-inst:
  cmd.run:
    - name: echo "dockers installed"

