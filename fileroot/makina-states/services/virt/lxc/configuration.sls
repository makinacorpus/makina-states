{% import "makina-states/_macros/h.jinja" as h with context %}
{%- set vmdata = salt['mc_cloud_vm.settings']() %}
{%- set data = vmdata.vts.lxc %}
{%- set extra_confs = {} %}
{%- set proc_mode = data.defaults.proc_mode %}
include:
  - makina-states.services.virt.lxc.hooks
  - makina-states.localsettings.apparmor
  - makina-states.services.virt.lxc.services

{% if grains['os'] in ['Ubuntu'] -%}
{% set extra_confs = {'/etc/init/lxc-net-makina.conf': {}} %}

{% elif grains['os'] in ['Debian'] -%}
{% set extra_confs = {'/etc/init.d/lxc-net-makina': {}} %}

# assume systemd
{% else %}
{% endif%}
{% do extra_confs.update({
  '/usr/bin/lxc-setup.sh': {},
  '/usr/bin/lxc-stop.sh': {},
  '/etc/systemd/system/lxc.service.d/lxc.conf': {'mode': "644"},
  '/etc/systemd/system/lxc-net-makina.service': {'mode': "644"}}) %}

{% set extra_confs = salt['mc_utils.copy_dictupdate'](
  data['host_confs'], extra_confs) %}
{% if grains['os'] in ['Ubuntu'] and grains['osrelease'] < '15.04' %}
{% do extra_confs.update({
     '/usr/bin/create_container_systemd_cgroup': {'mode': '755'},
     '/usr/bin/remove_container_systemd_cgroup': {'mode': '755'},
     '/usr/share/lxc/config/ubuntu.common.conf': {'mode': '644'}}) %}
{%  endif %}

{% macro rmacro() %}
    - watch_in:
      - mc_proxy: lxc-post-conf
    - watch:
      - mc_proxy: lxc-pre-conf
{% endmacro %}
{{ h.deliver_config_files(extra_confs, after_macro=rmacro, prefix='lxc-conf-')}}

lxc-conf-lxc-remove-files:
  file.absent:
    - names:
      - /etc/systemd/system/lxc.service
      {{rmacro()}}

lxc-conf-lxc-remove-files-reload:
  cmd.watch:
    - name: |
        if ! which systemctl >/dev/null 2>&1;then exit 0;fi
        if systemctl show lxc;then systemctl daemon-reload;fi
    - require:
      - mc_proxy: lxc-post-conf
    - watch:
      - file: lxc-conf-lxc-remove-files
    - watch_in:
      - mc_proxy: lxc-pre-restart

{% for i in ['/usr/share/lxc/config/common.conf'] %}
lxc-config-patch-{{i}}:
  cmd.run:
    - name: sed -re "s/proc:(mixed|ro|rw)/proc:{{proc_mode}}/g" -i "{{i}}"
    - onlyif: |
              set -ex
              test -e "{{i}}"
              grep "proc:" "{{i}}"|egrep -vq "proc:{{proc_mode}}"
  {{rmacro()}}
{% endfor%}
