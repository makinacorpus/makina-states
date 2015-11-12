{% import "makina-states/_macros/h.jinja" as h with context %}
{%- set vmdata = salt['mc_cloud_vm.settings']() %}
{%- set data = vmdata.vts.docker %}
{% set extra_confs = {} %}
include:
  - makina-states.services.virt.docker.hooks
  - makina-states.localsettings.apparmor
  - makina-states.services.virt.docker.services

{% if salt['mc_controllers.allow_lowlevel_states']() %}
{% if grains['os'] in ['Ubuntu'] -%}
{% set extra_confs = {'/etc/init/docker-net-makina.conf': {}} %}
{% elif grains['os'] in ['Debian'] -%}
{% set extra_confs = {'/etc/init.d/docker-net-makina': {}} %}
{% endif%}

{% set extra_confs = salt['mc_utils.copy_dictupdate'](
        data['host_confs'],
        extra_confs) %}

{% set url = data.binary_url %}
{% set fn = url.split('/')[-1] %}
{% set hash=data.hashes[fn]['hash'] %}
{% set dhash=data.hashes[fn]['dhash'] %}

{% macro rmacro() %}
    - watch:
      - file: docker-remove-symlinks1
      - file: docker-remove-symlinks2
      - mc_proxy: docker-pre-conf
    - watch_in:
      - mc_proxy: docker-post-conf
      - mc_proxy: docker-services-net
{% endmacro %}
{{ h.deliver_config_files(
     extra_confs, after_macro=rmacro, prefix='docker-conf-')}}

{# ubuntu systemd units are disabled for docker, wtf ... #}
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

{# as we wont run anymore systemd in docker, this is not needed anymore
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
    - name: xz -c -k -d "/opt/{{fn}}" > /usr/bin/docker
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
      - service: docker-services-net
    - watch_in:
      - mc_proxy: docker-post-conf
      - mc_proxy: docker-pre-hardrestart
#}
{# net service should not be restarted if running
   not to disrupt any connected docker #}
docker-services-net:
  service.running:
    - name: docker-net-makina
    - enable: True
    - watch:
      - file: docker-conf-/etc/default/magicbridge_docker1
      - file: docker-conf-/etc/dnsmasq.d/docker1
      - file: docker-conf-/etc/init/docker-net-makina.conf
      - file: docker-conf-/etc/systemd/system/docker-net-makina.service
      - file: docker-conf-/usr/bin/docker-net-makina.sh
    - watch_in:
      - mc_proxy: docker-post-conf
{%endif %}
