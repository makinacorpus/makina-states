{%- set vmdata = salt['mc_cloud_vm.settings']() %}
{%- set data = vmdata.vts.docker %}
{% set extra_confs = {} %}
include:
  - makina-states.services.virt.docker.hooks
  - makina-states.localsettings.apparmor
  - makina-states.services.virt.docker.services

{% if salt['mc_controllers.mastersalt_mode']() %}
{% if grains['os'] in ['Ubuntu'] -%}
{% set extra_confs = {'/etc/init/docker-net-makina.conf': {}} %}
{% elif grains['os'] in ['Debian'] -%}
{% set extra_confs = {'/etc/init.d/docker-net-makina': {}} %}
{% endif%}

{% set extra_confs = salt['mc_utils.copy_dictupdate'](
        data['host_confs'],
        extra_confs) %}

{# recently on ubuntu systemd units are disabled for
   docker, wtf ... #}

docker-conf:
  file.managed:
    - name: /etc/init/docker.conf
    - source: salt://makina-states/files/etc/init/docker.conf
    - makedirs: true
    - watch:
      - mc_proxy: docker-pre-conf
    - watch_in:
      - mc_proxy: docker-post-conf

docker-remove-symlinks2:
  file.absent:
    - name: /etc/systemd/system/docker.service
    - onlyif: test -h /etc/systemd/system/docker.service
    - watch:
      - mc_proxy: docker-pre-conf
    - watch_in:
      - mc_proxy: docker-post-conf
docker-remove-symlinks1:
  file.absent:
    - name: /etc/systemd/system/docker.socket
    - onlyif: test -h /etc/systemd/system/docker.socket
    - watch:
      - mc_proxy: docker-pre-conf
    - watch_in:
      - mc_proxy: docker-post-conf

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
      - file: docker-remove-symlinks1
      - file: docker-remove-symlinks2
      - mc_proxy: docker-pre-conf
    - watch_in:
      - mc_proxy: docker-post-conf
      - mc_proxy: docker-services-net
{% endfor %}

{% set url='https://github.com/makinacorpus/docker/releases/download/mc_1/docker-1.8-mc_3.txz' %}
{% set fn = url.split('/')[-1] %}
{% set hash='36ea74c00f42a37f65a31c84dce43f24' %}
{% set dhash='81d4391b879c0111c24bd222744dc483' %}
docker-replace-dist-binary:
  cmd.run:
    - name: |
            i=0
            while test -e "/usr/bin/docker.dist${i}";do
               i=$((i+1))
            done
            cp -f /usr/bin/docker "/usr/bin/docker.dist${i}"
    - onlyif: |
           set -e
           test -e /usr/bin/docker
           test "x$(md5sum /usr/bin/docker|awk '{print $1}')" != "x{{dhash}}"
    - watch:
      - mc_proxy: docker-pre-conf
    - watch_in:
      - mc_proxy: docker-post-conf
  file.managed:
    - source: "{{url}}"
    - source_hash: "md5={{hash}}"
    - name: "/opt/{{fn}}"
    - makedirs: true
    - user: root
    - group: root
    - mode: 755
    - watch:
      - mc_proxy: docker-pre-conf
    - watch_in:
      - mc_proxy: docker-post-conf
docker-replace-dist-binaryb:
  service.dead:
    - name: docker
    - onlyif: |
              if test -e /usr/bin/docker;then exit 0;fi
              test "x$(md5sum /usr/bin/docker|awk '{print $1}')" != "x{{dhash}}"
    - watch:
      - cmd: docker-replace-dist-binary
      - file: docker-replace-dist-binary
    - watch_in:
      - mc_proxy: docker-post-conf
      - mc_proxy: docker-pre-hardrestart
  cmd.run:
    - name: cd /usr/bin && tar xJvf "/opt/{{fn}}"
    - onlyif: |
              if test ! -e /usr/bin/docker;then exit 0;fi
              test "x$(md5sum /usr/bin/docker|awk '{print $1}')" != "x{{dhash}}"
    - watch:
      - service: docker-replace-dist-binaryb
      - cmd: docker-replace-dist-binary
      - file: docker-replace-dist-binary
    - watch_in:
      - mc_proxy: docker-post-conf
      - mc_proxy: docker-pre-hardrestart
  file.managed:
    - name: /usr/bin/docker
    - user: root
    - group: root
    - mode: 755
    - watch:
      - cmd: docker-replace-dist-binaryb
    - watch_in:
      - mc_proxy: docker-post-conf
      - mc_proxy: docker-pre-hardrestart
{# net service should not be restarted if running
   not to disrupt any connected docker #}
docker-services-net:
  service.running:
    - name: docker-net-makina
    - enable: True
    - require:
      - file: docker-replace-dist-binaryb
    - watch:
      - file: docker-conf-/etc/default/magicbridge_docker1
      - file: docker-conf-/etc/dnsmasq.d/docker1
      - file: docker-conf-/etc/init/docker-net-makina.conf
      - file: docker-conf-/etc/systemd/system/docker-net-makina.service
      - file: docker-conf-/usr/bin/docker-net-makina.sh
    - watch_in:
      - mc_proxy: docker-post-conf
{%endif %}
